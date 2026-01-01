import unittest
import uuid
import traceback
from app import create_app
from app.models import User, ContactRequest, get_db_connection
from datetime import date, timedelta

class Phase4TestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.unique_id = str(uuid.uuid4())[:8]

    def tearDown(self):
        self.app_context.pop()

    def test_cooldown_logic(self):
        """Test that set_cooldown updates status and next_eligible_date"""
        try:
            email = f'cool_{self.unique_id}@test.com'
            nni = f'NNI_{self.unique_id}'
            # User.create args: role, name, phone, email, password, city, blood_type=None, nni=None
            User.create('donor', 'Cool Donor', '555-' + self.unique_id, email, 'password', 'CityA', 'A+', nni)
            donor = User.get_by_email(email)
            
            # Test initial state
            self.assertTrue(donor.is_available)
            
            # Trigger cooldown
            donor.set_cooldown()
            
            # Reload donor
            donor = User.get_by_id(donor.id)
            
            self.assertFalse(donor.is_available)
            expected_date = date.today() + timedelta(days=90)
            self.assertEqual(donor.next_eligible_date, expected_date)
        except Exception:
            traceback.print_exc()
            raise
        
    def test_contact_revelation(self):
        """Test API for revealing contact info"""
        try:
            req_email = f'req_{self.unique_id}@test.com'
            don_email = f'don_{self.unique_id}@test.com'
            req_nni = f'NNI_R_{self.unique_id}'
            don_nni = f'NNI_D_{self.unique_id}'
            
            User.create('requester', 'Requester P4', '555-R' + self.unique_id, req_email, 'pass', 'City', None, req_nni)
            User.create('donor', 'Donor P4', '555-D' + self.unique_id, don_email, 'pass', 'City', 'O+', don_nni)
            
            requester = User.get_by_email(req_email)
            donor = User.get_by_email(don_email)
            
            # Create contact request
            ContactRequest.create(requester.id, donor.id)
            
            # Log in as requester
            with self.client.session_transaction() as sess:
                sess['user_id'] = requester.id
                sess['role'] = 'requester'
            
            # Try to get info (should fail/pending)
            response = self.client.get(f'/requester/get_contact_info/{donor.id}')
            data = response.get_json()
            self.assertFalse(data['success'])
            
            # Approve request manually in DB
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM contact_requests WHERE requester_id=%s AND donor_id=%s", (requester.id, donor.id))
            r_id = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            ContactRequest.update_status(r_id, 'approved')
            
            # Try again (should succeed)
            response = self.client.get(f'/requester/get_contact_info/{donor.id}')
            data = response.get_json()
            # print(data) # Debug
            self.assertTrue(data['success'])
            self.assertEqual(data['phone'], '555-D' + self.unique_id)
        except Exception:
            traceback.print_exc()
            raise

if __name__ == '__main__':
    unittest.main()
