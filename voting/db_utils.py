import sqlite3

DB_PATH = "db.sqlite3"

def get_db_connection():
    """Establish a connection to the SQLite3 database."""
    return sqlite3.connect(DB_PATH)

def fetch_all_voters():
    """Retrieve all voters."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Voters")
    voters = cursor.fetchall()
    conn.close()
    return voters

def fetch_elections():
    """Retrieve all elections."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Elections")
    elections = cursor.fetchall()
    conn.close()
    return elections
