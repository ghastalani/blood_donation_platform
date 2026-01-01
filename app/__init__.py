from flask import Flask
from config import Config
import mysql.connector

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize DB connection check (simple check)
    try:
        conn = mysql.connector.connect(
            host=app.config['DB_HOST'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {app.config['DB_NAME']}")
        conn.close()
        print(f"Database {app.config['DB_NAME']} checked/created.")
    except Exception as e:
        print(f"Error connecting to MySQL: {e}")

    # Language Support
    from flask import request, session, g
    from app.translations import get_text

    @app.before_request
    def before_request():
        g.lang = session.get('lang', 'en')

    @app.context_processor
    def inject_lang():
        # Unread message count for admin
        unread_count = 0
        if 'user_id' in session and session.get('role') == 'admin':
            from app.models import Message
            unread_count = Message.get_unread_count()
        
        return dict(
            lang=g.lang,
            get_text=lambda key: get_text(key, g.lang),
            dir='rtl' if g.lang == 'ar' else 'ltr',
            unread_message_count=unread_count
        )

    # Register Blueprints
    from app.routes import auth, donor, requester, admin, main
    app.register_blueprint(auth.bp)
    app.register_blueprint(donor.bp)
    app.register_blueprint(requester.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(main.bp)

    return app

