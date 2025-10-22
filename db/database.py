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
                files INTEGER,
                file_list TEXT
            )
        ''')
        # Add column if it doesn't exist for backward compatibility
        try:
            c.execute('ALTER TABLE seeds ADD COLUMN file_list TEXT')
        except sqlite3.OperationalError:
            # Column already exists
            pass
    except sqlite3.Error as e:
        print(e)

def insert_seed(conn, info_hash, name, size, files, file_list):
    """
    Create a new seed into the seeds table
    """
    sql = ''' INSERT OR IGNORE INTO seeds(info_hash,name,size,files,file_list)
              VALUES(?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (info_hash, name, size, files, file_list))
    conn.commit()
    return cur.lastrowid

def search_seeds(conn, query, min_size=None, max_size=None, min_files=None, max_files=None, sort_by='name', sort_order='asc'):
    """
    Query all rows in the seeds table with optional filtering and sorting.
    """
    sql = "SELECT id, info_hash, name, size, files FROM seeds WHERE name LIKE ?"
    params = ['%' + query + '%']

    if min_size is not None:
        sql += " AND size >= ?"
        params.append(min_size)
    if max_size is not None:
        sql += " AND size <= ?"
        params.append(max_size)
    if min_files is not None:
        sql += " AND files >= ?"
        params.append(min_files)
    if max_files is not None:
        sql += " AND files <= ?"
        params.append(max_files)

    if sort_by in ['name', 'size', 'files']:
        sql += f" ORDER BY {sort_by}"
        if sort_order.lower() == 'desc':
            sql += " DESC"
        else:
            sql += " ASC"

    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    return rows

def get_torrent_by_hash(conn, info_hash):
    """
    Query a torrent by its info_hash
    """
    cur = conn.cursor()
    cur.execute("SELECT id, info_hash, name, size, files, file_list FROM seeds WHERE info_hash=?", (info_hash,))
    rows = cur.fetchall()
    return rows

def get_latest_torrents(conn, limit=50, sort_by='id', sort_order='desc'):
    """
    Query the latest torrents with sorting
    """
    sql = "SELECT id, info_hash, name, size, files FROM seeds"

    if sort_by in ['id', 'name', 'size', 'files']:
        sql += f" ORDER BY {sort_by}"
        if sort_order.lower() == 'desc':
            sql += " DESC"
        else:
            sql += " ASC"
    else: # Default sort
        sql += " ORDER BY id DESC"

    sql += " LIMIT ?"

    cur = conn.cursor()
    cur.execute(sql, (limit,))
    rows = cur.fetchall()
    return rows

def clear_database(conn):
    """
    Delete all rows in the seeds table
    """
    sql = 'DELETE FROM seeds'
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
