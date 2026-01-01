import mysql.connector
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta

def get_db_connection():
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )
    return conn

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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (role, name, phone, email, hashed_password, city, blood_type, nni))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        if user_data:
            return User(**user_data)
        return None

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        if user_data:
            return User(**user_data)
        return None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_all_users():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [User(**r) for r in results]
    
    @staticmethod
    def check_nni_exists(nni):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE nni = %s", (nni,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists

    @staticmethod
    def get_active_donors(city=None, blood_type=None):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Check active AND available
        query = "SELECT id, name, city, blood_type, is_available, next_eligible_date FROM users WHERE (role = 'donor' OR role = 'both') AND is_active = 1"
        params = []
        if city:
            query += " AND city = %s"
            params.append(city)
        if blood_type:
            query += " AND blood_type = %s"
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
        cursor.execute("UPDATE users SET is_available = 0, next_eligible_date = %s WHERE id = %s", (next_date, self.id))
        conn.commit()
        cursor.close()
        conn.close()
        self.is_available = False
        self.next_eligible_date = next_date

    def set_cooldown(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        # Set next_eligible_date to 3 months from now
        next_date = date.today() + timedelta(days=90)
        cursor.execute("UPDATE users SET is_available = 0, next_eligible_date = %s WHERE id = %s", (next_date, self.id))
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
        cursor.execute("SELECT is_active FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            new_status = not result[0] # Toggle
            cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id))
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
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM donation_requests 
            WHERE status = 'open' 
            AND city = %s 
            AND blood_type_required = %s
            ORDER BY donation_date ASC
        """
        cursor.execute(query, (city, blood_type))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [DonationRequest(**r) for r in results]

    @staticmethod
    def get_by_id(request_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM donation_requests WHERE id = %s", (request_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return DonationRequest(**result)
        return None

    @staticmethod
    def create(requester_id, blood_type_required, city, hospital_location, donation_date, donation_time_start, donation_time_end, message):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO donation_requests (requester_id, blood_type_required, city, hospital_location, donation_date, donation_time_start, donation_time_end, message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (requester_id, blood_type_required, city, hospital_location, donation_date, donation_time_start, donation_time_end, message))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_requester(requester_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM donation_requests WHERE requester_id = %s ORDER BY created_at DESC"
        cursor.execute(query, (requester_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [DonationRequest(**r) for r in results]

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
            cursor.execute("INSERT INTO donations (request_id, donor_id) VALUES (%s, %s)", (request_id, donor_id))
            
            # Update request status to fulfilled (simple logic: 1 request = 1 donor for now)
            # Or keep open if multiple donors needed? Requirement says "Receive donation requests (only if available)".
            # Let's assume 1 request = 1 donor for simplicity unless broadcast.
            # Actually, if a donor accepts, they are committed.
            
            # Update donor availability
            # cursor.execute("UPDATE users SET is_available = FALSE WHERE id = %s", (donor_id,))
            # Wait, availability changes after donation is COMPLETED or when committed?
            # "After accepting... Donor becomes temporarily unavailable" -> So immediately on accept?
            # Let's say yes, to prevent double booking.
            
            cursor.execute("UPDATE users SET is_available = FALSE WHERE id = %s", (donor_id,))
            
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
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
            query = "INSERT INTO contact_requests (requester_id, donor_id, status) VALUES (%s, %s, 'pending')"
            cursor.execute(query, (requester_id, donor_id))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_requests_for_donor(donor_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Fetch request details + requester name
        query = """
            SELECT cr.*, u.name as requester_name 
            FROM contact_requests cr
            JOIN users u ON cr.requester_id = u.id
            WHERE cr.donor_id = %s AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
        """
        cursor.execute(query, (donor_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [ContactRequest(**r) for r in results]

    @staticmethod
    def update_status(request_id, status):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if status == 'approved':
                query = "UPDATE contact_requests SET status = %s, approved_at = NOW() WHERE id = %s"
            else:
                query = "UPDATE contact_requests SET status = %s WHERE id = %s"
            
            cursor.execute(query, (status, request_id))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def check_status(requester_id, donor_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) # Return dict to get timestamps
        query = "SELECT * FROM contact_requests WHERE requester_id = %s AND donor_id = %s"
        cursor.execute(query, (requester_id, donor_id))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result if result else None

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
            query = "INSERT INTO messages (name, email, message) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, email, message))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Message(**r) for r in results]

    @staticmethod
    def get_unread_count():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages WHERE is_read = FALSE")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count

    @staticmethod
    def mark_read(message_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET is_read = TRUE WHERE id = %s", (message_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
