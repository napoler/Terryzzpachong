import sqlite3

def create_database(db_file='seeds.db'):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS seeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            info_hash TEXT UNIQUE,
            name TEXT,
            size INTEGER,
            files INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def insert_seed(conn, info_hash, name, size, files):
    c = conn.cursor()
    try:
        c.execute("INSERT INTO seeds (info_hash, name, size, files) VALUES (?, ?, ?, ?)",
                  (info_hash, name, size, files))
        conn.commit()
    except sqlite3.IntegrityError:
        # Info hash already exists
        pass

def search_seeds(conn, query):
    c = conn.cursor()
    c.execute("SELECT * FROM seeds WHERE name LIKE ?", ('%' + query + '%',))
    results = c.fetchall()
    return results

if __name__ == '__main__':
    create_database()
