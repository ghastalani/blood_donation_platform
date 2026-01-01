from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.models import User, DonationRequest, get_db_connection

bp = Blueprint('admin', __name__, url_prefix='/admin')

def is_admin():
    return 'user_id' in session and session.get('role') == 'admin'

@bp.route('/dashboard')
def dashboard():
    if not is_admin():
        return redirect(url_for('auth.login'))
    
    # Simple stats
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='donor'")
    donor_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='requester'")
    requester_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM donation_requests WHERE status='open'")
    open_requests_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    return render_template('admin/dashboard.html', 
                           donor_count=donor_count, 
                           requester_count=requester_count, 
                           open_requests_count=open_requests_count)

@bp.route('/users')
def users():
    if not is_admin():
        return redirect(url_for('auth.login'))
    
    search = request.args.get('search', '')
    
    if search:
        # Search by name or email
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE name LIKE %s OR email LIKE %s ORDER BY created_at DESC"
        cursor.execute(query, (f'%{search}%', f'%{search}%'))
        users_list = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        users_list = [u.__dict__ for u in User.get_all_users()]
    
    return render_template('admin/users.html', users=users_list, search=search)

@bp.route('/toggle_user/<int:user_id>')
def toggle_user(user_id):
    if not is_admin():
        return redirect(url_for('auth.login'))
    
    if User.toggle_active(user_id):
        flash('User status updated.', 'success')
    else:
        flash('Error updating user.', 'danger')
    return redirect(url_for('admin.users'))

@bp.route('/broadcast', methods=['GET', 'POST'])
def broadcast():
    if not is_admin():
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        blood_type = request.form.get('blood_type')
        city = request.form.get('city')
        hospital = request.form.get('hospital')
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        message = request.form.get('message')
        
        # Admin ID as requester
        if DonationRequest.create(session['user_id'], blood_type, city, hospital, date, start_time, end_time, message):
            flash('Broadcast request created!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Error creating broadcast.', 'danger')

    return render_template('admin/broadcast.html')

@bp.route('/messages')
def messages():
    if not is_admin():
        return redirect(url_for('auth.login'))
    
    from app.models import Message
    messages_list = Message.get_all()
    
    return render_template('admin/messages.html', messages=messages_list)

@bp.route('/messages/<int:message_id>/read')
def mark_message_read(message_id):
    if not is_admin():
        return redirect(url_for('auth.login'))
    
    from app.models import Message
    Message.mark_read(message_id)
    flash('Message marked as read.', 'success')
    return redirect(url_for('admin.messages'))
