
import mysql.connector
from config import Config

def apply_migration():
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = conn.cursor()
        print("Connected to database.")
        
        # Alter blood_type column
        alter_query = "ALTER TABLE users MODIFY COLUMN blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown') DEFAULT NULL;"
        cursor.execute(alter_query)
        conn.commit()
        print("Successfully updated blood_type column to include 'Unknown'.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    apply_migration()
