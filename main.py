import tkinter as tk
from tkinter import scrolledtext
import threading
import sys
sys.path.append('crawler')
sys.path.append('db')
from dht_crawler import DHT
from database import create_database, search_seeds
import hashlib
import struct
import sqlite3

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("BTSeedAggregator")
        self.crawler_thread = None
        self.dht = None

        # Search frame
        search_frame = tk.Frame(root)
        search_frame.pack(pady=10)

        search_label = tk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=5)

        self.search_entry = tk.Entry(search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        search_button = tk.Button(search_frame, text="Search", command=self.search)
        search_button.pack(side=tk.LEFT, padx=5)

        # Results frame
        results_frame = tk.Frame(root)
        results_frame.pack(pady=10)

        results_label = tk.Label(results_frame, text="Results:")
        results_label.pack()

        self.results_listbox = tk.Listbox(results_frame, width=80, height=20)
        self.results_listbox.pack()

        # Log frame
        log_frame = tk.Frame(root)
        log_frame.pack(pady=10)

        log_label = tk.Label(log_frame, text="Log:")
        log_label.pack()

        self.log_widget = scrolledtext.ScrolledText(log_frame, width=80, height=10)
        self.log_widget.pack()

        # Buttons
        self.start_button = tk.Button(root, text="Start Crawler", command=self.start_crawler)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Stop Crawler", command=self.stop_crawler, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

    def start_crawler(self):
        self.log_widget.insert(tk.END, "Starting crawler...\n")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.crawler_thread = threading.Thread(target=self.run_crawler)
        self.crawler_thread.start()

    def stop_crawler(self):
        if self.dht:
            self.dht._break = True
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_widget.insert(tk.END, "Crawler stopped.\n")

    def run_crawler(self):
        conn = sqlite3.connect('seeds.db')
        self.dht = DHT(port=54767, version=b"XN\00\00", d=hashlib.sha1(b"This is a test !").digest(), db_file='seeds.db', log_callback=lambda s: self.log_widget.insert(tk.END, s + "\n"))
        self.dht.ping("".join(map(lambda x: chr(int(x)), "67.215.242.139".split("."))), struct.pack(">H", 6881))
        self.dht._network_thread()
        conn.close()

    def search(self):
        query = self.search_entry.get()
        results = search_seeds(query)
        self.results_listbox.delete(0, tk.END)
        for result in results:
            self.results_listbox.insert(tk.END, f"{result[2]} ({result[3]} bytes)")

def main():
    create_database()
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == '__main__':
    main()
