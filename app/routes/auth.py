from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.models import User
from app.translations import get_text

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Roles handling
        role = request.form.get('role')
        
        if not role or role not in ['donor', 'requester']:
            flash(get_text('role_required_error'), 'danger')
            return render_template('auth/register.html')

        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')
        city = request.form.get('city')
        blood_type = request.form.get('blood_type')
        nni = request.form.get('nni')

        # NNI Validation
        if nni and User.check_nni_exists(nni):
            flash(get_text('nni_exists_error'), 'danger')
            return render_template('auth/register.html')
        
        # Determine if blood type needed. Donors need it.
        if role == 'donor' and not blood_type:
             flash(get_text('blood_type_required_error'), 'danger')
             return render_template('auth/register.html')

        if User.create(role, name, phone, email, password, city, blood_type, nni):
            # Auto login
            user = User.get_by_email(email)
            if user:
                session['user_id'] = user.id
                session['role'] = user.role
                session['name'] = user.name
                
                # Show success modal/page or flash special message
                return render_template('auth/register_success.html', user=user)

            flash(get_text('registration_success'), 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(get_text('registration_failed'), 'danger')

    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.get_by_email(email)
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['name'] = user.name
            flash(get_text('login_success'), 'success')
            
            # Redirect based on role logic
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.is_donor: 
                 # Prefer donor dashboard if they are donor or both? 
                 # Or maybe a main dashboard? Let's default to donor dashboard for 'both' for now or create a unified one.
                 # Actually, requirements say "Student... show table of Donors". if 'both', do they see both?
                 # Let's send 'both' to donor dashboard, which should have link to requester view.
                 return redirect(url_for('donor.dashboard'))
            elif user.is_requester:
                return redirect(url_for('requester.dashboard'))
                
            return redirect(url_for('index')) # Fallback
        else:
            flash(get_text('invalid_credentials'), 'danger')
            
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash(get_text('logout_success'), 'info')
    return redirect(url_for('auth.login'))
