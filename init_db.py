import mysql.connector
from config import Config

def init_db():
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create DB if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")
        cursor.execute(f"USE {Config.DB_NAME}")
        
        # Read schema
        with open('schema.sql', 'r') as f:
            schema = f.read()
        
        # Execute schema
        # Split by ; to execute multiple statements
        statements = schema.split(';')
        for statement in statements:
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        print("Database initialized successfully.")
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == '__main__':
    init_db()
