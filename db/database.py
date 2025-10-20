import sqlite3

def create_connection(db_file):
    """ create a database connection to the SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """ create a table from the create_table_sql statement """
    try:
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
    except sqlite3.Error as e:
        print(e)

def insert_seed(conn, info_hash, name, size, files):
    """
    Create a new seed into the seeds table
    """
    sql = ''' INSERT OR IGNORE INTO seeds(info_hash,name,size,files)
              VALUES(?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (info_hash, name, size, files))
    conn.commit()
    return cur.lastrowid

def search_seeds(conn, query):
    """
    Query all rows in the seeds table
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM seeds WHERE name LIKE ?", ('%' + query + '%',))
    rows = cur.fetchall()
    return rows
