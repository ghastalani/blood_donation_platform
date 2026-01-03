import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta

def get_db_connection():
    # Get the database file path (relative to project root)
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    # Enable foreign key constraints in SQLite
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_database():
    """Initialize the database by creating all tables if they don't exist"""
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Read and execute schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = f.read()
    
    # Execute the schema (SQLite can handle multiple statements)
    cursor.executescript(schema)
    conn.commit()
    conn.close()


class User:
    def __init__(self, id, role, name, phone, email, password_hash, city, blood_type=None, nni=None, is_available=True, last_donation_date=None, next_eligible_date=None, is_active=True, created_at=None, **kwargs):
        self.id = id
        self.role = role
        self.name = name
        self.phone = phone
        self.email = email
        self.password_hash = password_hash
        self.city = city
        self.blood_type = blood_type
        self.nni = nni
        self.is_available = is_available
        self.last_donation_date = last_donation_date
        self.next_eligible_date = next_eligible_date
        self.is_active = is_active
        self.created_at = created_at

    @property
    def is_donor(self):
        return self.role in ['donor', 'both', 'admin']

    @property
    def is_requester(self):
        return self.role in ['requester', 'both', 'admin']

    @staticmethod
    def create(role, name, phone, email, password, city, blood_type=None, nni=None):
        # Strict Validation
        if len(phone) > 8:
            print("Validation Fail: Phone too long")
            return False
        if nni and len(nni) > 10:
            print("Validation Fail: NNI too long")
            return False
            
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO users (role, name, phone, email, password_hash, city, blood_type, nni)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (role, name, phone, email, hashed_password, city, blood_type, nni))
            conn.commit()
            return True
        except sqlite3.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        if user_data:
            return User(**dict(user_data))
        return None

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        if user_data:
            return User(**dict(user_data))
        return None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_all_users():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [User(**dict(r)) for r in results]
    
    @staticmethod
    def check_nni_exists(nni):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE nni = ?", (nni,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists

    @staticmethod
    def get_active_donors(city=None, blood_type=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        # Check active AND available
        query = "SELECT id, name, city, blood_type, is_available, next_eligible_date FROM users WHERE (role = 'donor' OR role = 'both') AND is_active = 1"
        params = []
        if city:
            query += " AND city = ?"
            params.append(city)
        if blood_type:
            query += " AND blood_type = ?"
            params.append(blood_type)
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results

    def set_cooldown(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        # Set next_eligible_date to 3 months from now
        next_date = date.today() + timedelta(days=90)
        cursor.execute("UPDATE users SET is_available = 0, next_eligible_date = ? WHERE id = ?", (next_date, self.id))
        conn.commit()
        cursor.close()
        conn.close()
        self.is_available = False
        self.next_eligible_date = next_date


    @staticmethod
    def toggle_active(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        # First get current status
        cursor.execute("SELECT is_active FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            new_status = not result[0] # Toggle
            cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        cursor.close()
        conn.close()
        return False

class DonationRequest:
    def __init__(self, id, requester_id, blood_type_required, city, hospital_location, donation_date, donation_time_start, donation_time_end, message, status, created_at, is_broadcast, **kwargs):
        self.id = id
        self.requester_id = requester_id
        self.blood_type_required = blood_type_required
        self.city = city
        self.hospital_location = hospital_location
        self.donation_date = donation_date
        self.donation_time_start = donation_time_start
        self.donation_time_end = donation_time_end
        self.message = message
        self.status = status
        self.created_at = created_at
        self.is_broadcast = is_broadcast

    @staticmethod
    def get_open_requests(city, blood_type):
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT * FROM donation_requests 
            WHERE status = 'open' 
            AND city = ? 
            AND blood_type_required = ?
            ORDER BY donation_date ASC
        """
        cursor.execute(query, (city, blood_type))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [DonationRequest(**dict(r)) for r in results]

    @staticmethod
    def get_by_id(request_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM donation_requests WHERE id = ?", (request_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return DonationRequest(**dict(result))
        return None

    @staticmethod
    def create(requester_id, blood_type_required, city, hospital_location, donation_date, donation_time_start, donation_time_end, message):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO donation_requests (requester_id, blood_type_required, city, hospital_location, donation_date, donation_time_start, donation_time_end, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (requester_id, blood_type_required, city, hospital_location, donation_date, donation_time_start, donation_time_end, message))
            conn.commit()
            return True
        except sqlite3.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_requester(requester_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM donation_requests WHERE requester_id = ? ORDER BY created_at DESC"
        cursor.execute(query, (requester_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [DonationRequest(**dict(r)) for r in results]

class Donation:
    def __init__(self, id, request_id, donor_id, status, completed_at, **kwargs):
        self.id = id
        self.request_id = request_id
        self.donor_id = donor_id
        self.status = status
        self.completed_at = completed_at

    @staticmethod
    def create(request_id, donor_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Create donation record
            cursor.execute("INSERT INTO donations (request_id, donor_id) VALUES (?, ?)", (request_id, donor_id))
            
            # Update donor availability
            cursor.execute("UPDATE users SET is_available = 0 WHERE id = ?", (donor_id,))
            
            conn.commit()
            return True
        except sqlite3.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

class ContactRequest:
    def __init__(self, id, requester_id, donor_id, status, created_at, approved_at=None, requester_name=None, **kwargs):
        self.id = id
        self.requester_id = requester_id
        self.donor_id = donor_id
        self.status = status
        self.created_at = created_at
        self.approved_at = approved_at
        self.requester_name = requester_name

    @staticmethod
    def create(requester_id, donor_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = "INSERT INTO contact_requests (requester_id, donor_id, status) VALUES (?, ?, 'pending')"
            cursor.execute(query, (requester_id, donor_id))
            conn.commit()
            return True
        except sqlite3.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_requests_for_donor(donor_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        # Fetch request details + requester name
        query = """
            SELECT cr.*, u.name as requester_name 
            FROM contact_requests cr
            JOIN users u ON cr.requester_id = u.id
            WHERE cr.donor_id = ? AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
        """
        cursor.execute(query, (donor_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [ContactRequest(**dict(r)) for r in results]

    @staticmethod
    def update_status(request_id, status):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if status == 'approved':
                query = "UPDATE contact_requests SET status = ?, approved_at = datetime('now') WHERE id = ?"
            else:
                query = "UPDATE contact_requests SET status = ? WHERE id = ?"
            
            cursor.execute(query, (status, request_id))
            conn.commit()
            return True
        except sqlite3.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def check_status(requester_id, donor_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM contact_requests WHERE requester_id = ? AND donor_id = ?"
        cursor.execute(query, (requester_id, donor_id))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return dict(result) if result else None

class Message:
    def __init__(self, id, name, email, message, is_read, created_at, **kwargs):
        self.id = id
        self.name = name
        self.email = email
        self.message = message
        self.is_read = is_read
        self.created_at = created_at

    @staticmethod
    def create(name, email, message):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)"
            cursor.execute(query, (name, email, message))
            conn.commit()
            return True
        except sqlite3.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Message(**dict(r)) for r in results]

    @staticmethod
    def get_unread_count():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages WHERE is_read = 0")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count

    @staticmethod
    def mark_read(message_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (message_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
