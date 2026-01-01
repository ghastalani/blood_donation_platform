from app import create_app
from app.models import User, ContactRequest, get_db_connection
import uuid
from datetime import date, timedelta

app = create_app()
app.app_context().push()

unique_id = str(uuid.uuid4())[:8]
print(f"Testing with Unique ID: {unique_id}")

try:
    # 1. Cooldown Test
    print("--- Testing Cooldown ---")
    email = f'cool_{unique_id}@test.com'
    nni = f'NNI_{unique_id}'
    User.create('donor', 'Cool Donor', '555-' + unique_id, email, 'password', 'CityA', 'A+', nni)
    donor = User.get_by_email(email)
    
    if donor.is_available:
        print("Donor initially available: OK")
    else:
        print("Donor initially available: FAIL")
        
    donor.set_cooldown()
    
    donor = User.get_by_id(donor.id)
    if not donor.is_available and donor.next_eligible_date == date.today() + timedelta(days=90):
        print("Donor cooldown set: OK")
    else:
        print(f"Donor cooldown set: FAIL (Available: {donor.is_available}, Date: {donor.next_eligible_date})")

    # 2. Contact Revelation Test
    print("--- Testing Contact Revelation ---")
    req_email = f'req_{unique_id}@test.com'
    don_email = f'don_{unique_id}@test.com'
    
    User.create('requester', 'Requester P4', '555-R' + unique_id, req_email, 'pass', 'City', None, f'NNI_R_{unique_id}')
    User.create('donor', 'Donor P4', '555-D' + unique_id, don_email, 'pass', 'City', 'O+', f'NNI_D_{unique_id}')
    
    requester = User.get_by_email(req_email)
    donor = User.get_by_email(don_email)
    
    # Create request
    if ContactRequest.create(requester.id, donor.id):
        print("Contact Request created: OK")
    else:
        print("Contact Request created: FAIL")
        
    # Approve it
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM contact_requests WHERE requester_id=%s AND donor_id=%s", (requester.id, donor.id))
    r_id = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    ContactRequest.update_status(r_id, 'approved')
    print("Request approved manually.")
    
    # Check status via model
    status = ContactRequest.check_status(requester.id, donor.id)
    if status == 'approved':
        print("Status check approved: OK")
    else:
        print(f"Status check approved: FAIL ({status})")
        
except Exception as e:
    print(f"EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
