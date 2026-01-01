
import mysql.connector
from config import Config

def apply_migration_phase2():
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = conn.cursor()
        print("Connected to database.")
        
        # 1. Update role ENUM to include 'both'
        print("Updating role column...")
        cursor.execute("ALTER TABLE users MODIFY COLUMN role ENUM('donor', 'requester', 'admin', 'both') NOT NULL;")
        
        # 2. Add blood_type 'Unknown' if not exists (already done, but good to ensure consistency in ENUM definition)
        print("Updating blood_type column...")
        cursor.execute("ALTER TABLE users MODIFY COLUMN blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown') DEFAULT NULL;")
        
        # 3. Create contact_requests table
        print("Creating contact_requests table...")
        create_contact_requests = """
        CREATE TABLE IF NOT EXISTS contact_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            requester_id INT NOT NULL,
            donor_id INT NOT NULL,
            status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (requester_id) REFERENCES users (id),
            FOREIGN KEY (donor_id) REFERENCES users (id),
            UNIQUE KEY unique_request (requester_id, donor_id)
        );
        """
        cursor.execute(create_contact_requests)
        
        conn.commit()
        print("Migration Phase 2 completed successfully.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    apply_migration_phase2()
