import mysql.connector
from config import Config

def migrate():
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )
    cursor = conn.cursor()
    
    try:
        print("Checking for approved_at column in contact_requests...")
        # Check if column exists
        cursor.execute("SHOW COLUMNS FROM contact_requests LIKE 'approved_at'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding approved_at column...")
            cursor.execute("ALTER TABLE contact_requests ADD COLUMN approved_at DATETIME DEFAULT NULL")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column already exists.")
            
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
