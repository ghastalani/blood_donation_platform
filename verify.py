import requests
import time
from threading import Thread
from run import app

# Server assumed to be running externally
BASE_URL = "http://localhost:5000" # Default flask port
SESSION = requests.Session()

def test_flow():
    print("Starting Verification...")

    # 1. Register Donor
    print("1. Registering Donor...")
    res = SESSION.post(f"{BASE_URL}/auth/register", data={
        "role": "donor",
        "name": "John Donor",
        "phone": "1234567890",
        "email": "john@example.com",
        "password": "password123",
        "city": "New York",
        "blood_type": "A+",
        "nni": "NNI123"
    })
    if res.status_code == 200 and "Login" in res.text:
        print("   -> Donor Registration Successful")
    else:
        # Might fail if already exists, which is fine for re-runs
        print(f"   -> Donor Registration Status: {res.status_code}")

    # 2. Login Donor
    print("2. Logging in Donor...")
    res = SESSION.post(f"{BASE_URL}/auth/login", data={
        "email": "john@example.com",
        "password": "password123"
    })
    if res.status_code == 200 and "Donor Dashboard" in res.text:
        print("   -> Donor Login Successful")
    else:
        print(f"   -> Donor Login Failed: {res.status_code}")
        print(f"   -> Response: {res.text}")
        return

    # 3. Register Requester
    print("3. Registering Requester...")
    SESSION.cookies.clear() # Clear session
    res = SESSION.post(f"{BASE_URL}/auth/register", data={
        "role": "requester",
        "name": "Jane Requester",
        "phone": "0987654321",
        "email": "jane@example.com",
        "password": "password123",
        "city": "New York"
    })
    if res.status_code == 200:
        print("   -> Requester Registration Status: {res.status_code}")

    # 4. Login Requester
    print("4. Logging in Requester...")
    res = SESSION.post(f"{BASE_URL}/auth/login", data={
        "email": "jane@example.com",
        "password": "password123"
    })
    if res.status_code == 200 and "Requester Dashboard" in res.text:
        print("   -> Requester Login Successful")
    else:
        print(f"   -> Requester Login Failed: {res.status_code}")
        print(f"   -> Response: {res.text}")
        return

    # 5. Create Request
    print("5. Creating Request...")
    res = SESSION.post(f"{BASE_URL}/requester/create_request", data={
        "blood_type": "A+",
        "city": "New York",
        "hospital": "City Hospital",
        "date": "2024-12-31",
        "start_time": "10:00",
        "end_time": "12:00",
        "message": "Urgent need"
    })
    if res.status_code == 200 and "Request created successfully" in res.text:
        print("   -> Request Creation Successful")
    else:
        print(f"   -> Request Creation Failed: {res.status_code}")
        print(f"   -> Response: {res.text}")
        # Continue anyway to see if we can accept (maybe previous run created it)

    # 6. Donor Accepts Request
    print("6. Donor Accepting Request...")
    SESSION.cookies.clear()
    SESSION.post(f"{BASE_URL}/auth/login", data={"email": "john@example.com", "password": "password123"})
    
    # Try to find request ID. Since we can't parse easily, we try ID 1.
    # If ID 1 doesn't exist, we might fail.
    # But wait, if previous run created request (and failed to log success), maybe ID is 1?
    # But debug_db said Requests: []. So no requests exist.
    # So this step will likely fail if Step 5 failed.
    
    res = SESSION.get(f"{BASE_URL}/donor/accept/1")
    if res.status_code == 200 and "You are now marked as unavailable" in res.text:
        print("   -> Request Accepted Successful")
    else:
        print(f"   -> Request Accept Failed: {res.status_code}")
        # print(f"   -> Response: {res.text}") 

    # 7. Verify Donor Unavailable
    print("7. Verifying Donor Unavailable...")
    res = SESSION.get(f"{BASE_URL}/donor/dashboard")
    if "Unavailable" in res.text:
        print("   -> Donor is Unavailable (Correct)")
    else:
        print("   -> Donor is Available (Incorrect)")

    print("Verification Complete.")

if __name__ == "__main__":
    try:
        test_flow()
    except Exception as e:
        print(f"Error: {e}")
