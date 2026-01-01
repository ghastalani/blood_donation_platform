from app import create_app
from app.models import User, get_db_connection
from werkzeug.security import generate_password_hash

app = create_app()
app.app_context().push()

def manage_admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check for admin
    cursor.execute("SELECT * FROM users WHERE role = 'admin' LIMIT 1")
    admin = cursor.fetchone()
    
    email = 'admin@blooddonation.com'
    password = 'admin'
    
    if admin:
        print(f"Admin account found: {admin['email']}")
        # Reset password to ensure user can login
        print(f"Resetting password to: {password}")
        
        hashed_pw = generate_password_hash(password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hashed_pw, admin['id']))
        conn.commit()
        print("Password reset successfully.")
        email = admin['email']
    else:
        print("No admin found. Creating one...")
        from app.models import User
        # role, name, phone, email, password, city, blood_type, nni
        if User.create('admin', 'System Admin', '000-000-0000', email, password, 'HQ', 'O+', 'ADMIN_001'):
            print("Admin account created successfully.")
        else:
            print("Failed to create admin.")
            
    cursor.close()
    conn.close()
    
    print("-" * 20)
    print(f"Email: {email}")
    print(f"Password: {password}")
    print("-" * 20)

if __name__ == "__main__":
    manage_admin()
