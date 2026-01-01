import mysql.connector
from config import Config

def check_user():
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, role FROM users")
    users = cursor.fetchall()
    print(f"Users: {users}")
    
    cursor.execute("SELECT * FROM donations")
    donations = cursor.fetchall()
    print(f"Donations: {donations}")

    cursor.execute("SELECT id, blood_type_required, city FROM donation_requests")
    requests = cursor.fetchall()
    print(f"Requests: {requests}")
    
    conn.close()

if __name__ == '__main__':
    check_user()
