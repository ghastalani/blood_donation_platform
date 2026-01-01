
import unittest
from app import create_app
from app.models import User
import mysql.connector
from config import Config

class FeaturesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
        
        # Reset DB slightly if needed, or just test logic
        # For simplicity, we assume DB is running and reachable.
        
    def test_home_page_en(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['lang'] = 'en'
            response = c.get('/')
            self.assertIn(b'Welcome to the Blood Donation Platform', response.data)
            self.assertIn(b'Connecting donors with those in need.', response.data)

    def test_home_page_ar(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['lang'] = 'ar'
            response = c.get('/')
            # Use unicode string for arabic check
            self.assertTrue('مرحباً بكم في منصة التبرع بالدم' in response.data.decode('utf-8'))
            self.assertIn('dir="rtl"', response.data.decode('utf-8'))

    def test_unknown_blood_type(self):
        # We will try to create a user via model directly to test DB constraint
        email = "test_unknown@example.com"
        phone = "0000000000"
        
        # Cleanup first
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email = %s", (email,))
        conn.commit()
        cursor.close()
        conn.close()

        result = User.create(
            role='donor',
            name='Test Unknown',
            phone=phone,
            email=email,
            password='password',
            city='Test City',
            blood_type='Unknown',
            nni='123456789'
        )
        self.assertTrue(result)
        
        user = User.get_by_email(email)
        self.assertIsNotNone(user)
        self.assertEqual(user.blood_type, 'Unknown')
        
        # Cleanup
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user.id,))
        conn.commit()
        cursor.close()
        conn.close()

if __name__ == '__main__':
    unittest.main()
