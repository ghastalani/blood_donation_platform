from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.models import User, DonationRequest

bp = Blueprint('requester', __name__, url_prefix='/requester')

@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or not session.get('role') in ['requester', 'both', 'admin']:
        return redirect(url_for('auth.login'))
    
    requests = DonationRequest.get_by_requester(session['user_id'])
    return render_template('requester/dashboard.html', requests=requests)

@bp.route('/create_request', methods=['GET', 'POST'])
def create_request():
    if 'user_id' not in session or not session.get('role') in ['requester', 'both', 'admin']:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        blood_type = request.form.get('blood_type')
        city = request.form.get('city')
        hospital = request.form.get('hospital')
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        message = request.form.get('message')
        
        if DonationRequest.create(session['user_id'], blood_type, city, hospital, date, start_time, end_time, message):
            flash('Request created successfully!', 'success')
            return redirect(url_for('requester.dashboard'))
        else:
            flash('Error creating request.', 'danger')
            
    return render_template('requester/create_request.html')

@bp.route('/browse_donors', methods=['GET', 'POST'])
def browse_donors():
    if 'user_id' not in session or not session.get('role') in ['requester', 'both', 'admin']:
        return redirect(url_for('auth.login'))
    
    city = request.args.get('city')
    blood_type = request.args.get('blood_type')
    
    donors = User.get_active_donors(city, blood_type)
    
    return render_template('requester/browse_donors.html', donors=donors)

@bp.route('/request_contact/<int:donor_id>', methods=['GET', 'POST'])
def request_contact(donor_id):
    if 'user_id' not in session or not session.get('role') in ['requester', 'both', 'admin']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
             return {'success': False, 'message': 'Unauthorized'}, 401
        return redirect(url_for('auth.login'))
        
    from app.models import ContactRequest
    
    # Check if request is AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    status = ContactRequest.check_status(session['user_id'], donor_id)
    
    if status == 'pending':
        msg = 'Request already pending.'
        if is_ajax:
             return {'success': False, 'message': msg, 'status': 'pending'}
        flash(msg, 'warning')
    elif status == 'approved':
         msg = 'Request already approved.'
         if is_ajax:
              return {'success': False, 'message': msg, 'status': 'approved'}
         flash(msg, 'info')
    elif ContactRequest.create(session['user_id'], donor_id):
        msg = 'Contact request sent!'
        if is_ajax:
             return {'success': True, 'message': msg, 'status': 'pending'}
        flash(msg, 'success')
    else:
        msg = 'Error sending request.'
        if is_ajax:
             return {'success': False, 'message': msg}
        flash(msg, 'danger')
        
    return redirect(url_for('requester.browse_donors'))
    return redirect(url_for('requester.browse_donors'))

@bp.route('/get_contact_info/<int:donor_id>')
def get_contact_info(donor_id):
    if 'user_id' not in session:
        return {'success': False, 'message': 'Unauthorized'}, 401
    
    from app.models import ContactRequest, User
    from datetime import datetime, timedelta
    
    status_record = ContactRequest.check_status(session['user_id'], donor_id)
    
    if status_record and status_record['status'] == 'approved':
        # Check expiry
        if status_record['approved_at']:
            approved_at = status_record['approved_at']
            # Ensure approved_at is datetime
            if isinstance(approved_at, str):
                try:
                    approved_at = datetime.strptime(approved_at, '%Y-%m-%d %H:%M:%S')
                except:
                     pass # Fallback or error
            
            expiry_time = approved_at + timedelta(minutes=10)
            if datetime.now() > expiry_time:
                return {'success': False, 'message': 'Contact info expired. 10 minute window closed.'}
                
            donor = User.get_by_id(donor_id)
            if donor:
                return {
                    'success': True,
                    'name': donor.name,
                    'phone': donor.phone,
                    'email': donor.email,
                    'expires_at': expiry_time.isoformat()
                }
    
    return {'success': False, 'message': 'Not approved, not found, or expired.'}
