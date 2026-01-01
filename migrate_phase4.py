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
        print("Checking for next_eligible_date column...")
        cursor.execute("SHOW COLUMNS FROM users LIKE 'next_eligible_date'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding next_eligible_date column...")
            cursor.execute("ALTER TABLE users ADD COLUMN next_eligible_date DATE")
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
