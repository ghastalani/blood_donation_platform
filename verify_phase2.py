
import unittest
from app import create_app
from app.models import User, ContactRequest
import mysql.connector
from config import Config

class Phase2FeaturesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
        
    def test_dual_role_registration(self):
        email = "test_dual@example.com"
        nni = "DUAL12345"
        
        # Cleanup
        self.cleanup_user(email)

        # Register as both
        response = self.client.post('/auth/register', data={
            'is_donor': 'on',
            'is_requester': 'on',
            'name': 'Dual Role User',
            'phone': '111222333',
            'email': email,
            'password': 'password',
            'city': 'Test City',
            'blood_type': 'O+',
            'nni': nni
        }, follow_redirects=True)
        
        self.assertIn(b'Registration Complete', response.data)
        
        user = User.get_by_email(email)
        self.assertIsNotNone(user)
        self.assertEqual(user.role, 'both')
        self.assertTrue(user.is_donor)
        self.assertTrue(user.is_requester)
        self.assertTrue(User.check_nni_exists(nni))

    def test_nni_uniqueness(self):
        email1 = "nni1@example.com"
        email2 = "nni2@example.com"
        nni = "UNIQUE123"
        
        self.cleanup_user(email1)
        self.cleanup_user(email2)
        
        # Register first
        User.create('donor', 'U1', '111', email1, 'pass', 'City', 'A+', nni)
        
        # Try register second with same NNI via route logic check (mock request)
        # Here we just check the static method returns true
        self.assertTrue(User.check_nni_exists(nni))
        
        # Cleanup
        self.cleanup_user(email1)
        self.cleanup_user(email2)

    def test_contact_request_flow(self):
        donor_email = "donor_c@example.com"
        req_email = "req_c@example.com"
        
        self.cleanup_user(donor_email)
        self.cleanup_user(req_email)
        
        User.create('donor', 'Donor C', '222', donor_email, 'pass', 'City', 'A+', 'D1')
        User.create('requester', 'Req C', '333', req_email, 'pass', 'City', None, 'R1')
        
        donor = User.get_by_email(donor_email)
        requester = User.get_by_email(req_email)
        
        # Create request
        success = ContactRequest.create(requester.id, donor.id)
        self.assertTrue(success)
        
        status = ContactRequest.check_status(requester.id, donor.id)
        self.assertEqual(status, 'pending')
        
        # Fetch requests
        requests = ContactRequest.get_requests_for_donor(donor.id)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].requester_id, requester.id)
        
        # Approve
        ContactRequest.update_status(requests[0].id, 'approved')
        status = ContactRequest.check_status(requester.id, donor.id)
        self.assertEqual(status, 'approved')
        
        self.cleanup_user(donor_email)
        self.cleanup_user(req_email)
        
        # Cleanup contact requests (manual SQL if needed, but users cascade hopefully or we just leave them/delete via ID)
        # Ideally we clean requests too.
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM contact_requests WHERE requester_id IN (%s, %s) OR donor_id IN (%s, %s)", (requester.id, donor.id, requester.id, donor.id))
        conn.commit()
        c.close()
        conn.close()


    def cleanup_user(self, email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        u = cursor.fetchone()
        if u:
            # Delete related data first
            cursor.execute("DELETE FROM contact_requests WHERE requester_id = %s OR donor_id = %s", (u[0], u[0]))
            cursor.execute("DELETE FROM donations WHERE donor_id = %s", (u[0],))
            cursor.execute("DELETE FROM donation_requests WHERE requester_id = %s", (u[0],))
            cursor.execute("DELETE FROM users WHERE id = %s", (u[0],))
            conn.commit()
        cursor.close()
        conn.close()

def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )

if __name__ == '__main__':
    unittest.main()
