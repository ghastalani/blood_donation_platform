# Mock Email Service
import time

def send_email(to_email, subject, body):
    """
    Mock email sending function.
    In a real app, this would use SMTP or an API like SendGrid/Mailgun.
    """
    print(f"--- MOCK EMAIL START ---")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print(f"--- MOCK EMAIL END ---")
    return True
