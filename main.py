import argparse
import sys
sys.path.append('crawler')
from dht_crawler import DHT
from db.database import create_database, search_seeds
import hashlib
import struct
import sqlite3

def main():
    parser = argparse.ArgumentParser(description='BTSeedAggregator')
    parser.add_argument('command', choices=['crawl', 'search'], help='Command to execute')
    parser.add_argument('--query', help='Search query')
    args = parser.parse_args()

    if args.command == 'crawl':
        print('Starting crawler...')
        conn = sqlite3.connect('seeds.db')
        d = DHT(port=54767, version="XN\00\00".encode('utf-8'), d=hashlib.sha1("This is a test !".encode('utf-8')).digest(), db_conn=conn)
        d.ping("".join(map(lambda x: chr(int(x)), "67.215.242.139".split("."))), struct.pack(">H", 6881))
        d._network_thread(iterations=5)
        conn.close()
        print("Crawler finished.")
    elif args.command == 'search':
        if not args.query:
            print('Please provide a search query with --query')
            return
        print(f'Searching for: {args.query}')
        results = search_seeds(args.query)
        for result in results:
            print(result)

if __name__ == '__main__':
    create_database()
    main()
