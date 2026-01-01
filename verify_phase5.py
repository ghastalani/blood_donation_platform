import unittest
import uuid
import traceback
import time
from datetime import datetime, timedelta
from app import create_app
from app.models import User, ContactRequest, get_db_connection

class Phase5TestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.unique_id = str(uuid.uuid4())[:8]

    def tearDown(self):
        self.app_context.pop()

    def test_contact_expiry_logic(self):
        """Test contact info visibility 10-min expiry"""
        try:
            req_email = f'req_{self.unique_id}@test.com'
            don_email = f'don_{self.unique_id}@test.com'
            
            # Create users
            User.create('requester', 'Req P5', '555-R', req_email, 'pass', 'City', None, f'N_R_{self.unique_id}')
            User.create('donor', 'Don P5', '555-D', don_email, 'pass', 'City', 'O+', f'N_D_{self.unique_id}')
            
            requester = User.get_by_email(req_email)
            donor = User.get_by_email(don_email)
            
            # Create and Approve request
            ContactRequest.create(requester.id, donor.id)
            
            # Find Request ID
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM contact_requests WHERE requester_id=%s AND donor_id=%s", (requester.id, donor.id))
            r_id = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            ContactRequest.update_status(r_id, 'approved')
            
            # Login as requester
            with self.client.session_transaction() as sess:
                sess['user_id'] = requester.id
                sess['role'] = 'requester'
                
            # 1. Check immediately (Should be visible)
            response = self.client.get(f'/requester/get_contact_info/{donor.id}')
            data = response.get_json()
            self.assertTrue(data['success'], "Contact info should be visible immediately after approval.")
            
            # 2. Manipulate timestamp to 11 minutes ago
            conn = get_db_connection()
            cursor = conn.cursor()
            expired_time = datetime.now() - timedelta(minutes=11)
            cursor.execute("UPDATE contact_requests SET approved_at = %s WHERE id = %s", (expired_time, r_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            # 3. Check again (Should be expired)
            response = self.client.get(f'/requester/get_contact_info/{donor.id}')
            data = response.get_json()
            self.assertFalse(data['success'], "Contact info should be expired after 10 minutes.")
            self.assertIn("expired", data['message'].lower())
            
        except Exception:
            traceback.print_exc()
            raise

if __name__ == '__main__':
    unittest.main()
