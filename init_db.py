import sqlite3
import os

def init_db():
    try:
        # Get database path
        db_path = os.path.join(os.path.dirname(__file__), 'app.db')
        
        conn = sqlite3.connect(db_path)
        # Enable foreign key constraints
        conn.execute('PRAGMA foreign_keys = ON')
        cursor = conn.cursor()
        
        # Read schema
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()
        
        # Execute schema (SQLite can handle multiple statements with executescript)
        cursor.executescript(schema)
        
        conn.commit()
        print("Database initialized successfully.")
        print(f"Database created at: {db_path}")
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == '__main__':
    init_db()
