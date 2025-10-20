import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys
from crawler import Crawler
from db.database import create_database, search_seeds
import sqlite3
import ctypes

class App:
    def __init__(self, root):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            pass
        self.root = root
        self.root.title("BTSeedAggregator")
        self.crawler_thread = None
        self.crawler = None

        self.create_menu()

        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar = ttk.Frame(main_frame, width=150)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Search bar
        search_frame = ttk.Frame(content_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=5)

        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        search_button = ttk.Button(search_frame, text="Search", command=self.search)
        search_button.pack(side=tk.LEFT, padx=5)

        # Results table
        results_frame = ttk.Frame(content_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_tree = ttk.Treeview(results_frame, columns=('Name', 'Size', 'Files'), show='headings')
        self.results_tree.heading('Name', text='Name')
        self.results_tree.heading('Size', text='Size')
        self.results_tree.bind('<Button-3>', self.show_context_menu)
        self.results_tree.heading('Files', text='Files')
        self.results_tree.pack(fill=tk.BOTH, expand=True)

        # Bottom panel
        bottom_panel = ttk.Frame(main_frame, height=100)
        bottom_panel.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Log frame
        log_frame = ttk.Frame(bottom_panel)
        log_frame.pack(fill=tk.BOTH, expand=True)

        log_label = ttk.Label(log_frame, text="Log:")
        log_label.pack(anchor=tk.W)

        self.log_widget = scrolledtext.ScrolledText(log_frame, height=5)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        # Buttons are now in the menu

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Start Crawler", command=self.start_crawler)
        tools_menu.add_command(label="Stop Crawler", command=self.stop_crawler)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings", command=self.open_settings)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.open_about)

    def open_settings(self):
        pass

    def open_about(self):
        pass

    def start_crawler(self):
        self.log_widget.insert(tk.END, "Starting crawler...\n")
        self.crawler = Crawler('seeds.db')
        self.crawler_thread = threading.Thread(target=self.crawler.run)
        self.crawler_thread.start()

    def stop_crawler(self):
        if self.crawler:
            self.crawler.stop()
        self.log_widget.insert(tk.END, "Crawler stopped.\n")

    def show_context_menu(self, event):
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Find Related", command=self.find_related)
            context_menu.post(event.x_root, event.y_root)

    def find_related(self):
        selected_item = self.results_tree.selection()[0]
        name = self.results_tree.item(selected_item)['values'][0]
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, name)
        self.search()

    def search(self):
        query = self.search_entry.get()
        conn = sqlite3.connect('seeds.db')
        results = search_seeds(conn, query)
        conn.close()
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)
        for result in results:
            self.results_tree.insert('', 'end', values=(result[2], result[3], result[4]))

def main():
    create_database()
    root = tk.Tk()
    app = App(root)
    root.after(5000, app.start_crawler)
    root.mainloop()

if __name__ == '__main__':
    main()
