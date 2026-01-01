from flask import Blueprint, render_template, session, redirect, request, url_for

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'ar']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    from flask import flash
    if request.method == 'POST':
        from app.models import Message
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if Message.create(name, email, message):
            flash('Thank you for your message. We will respond soon.', 'success')
            return redirect(url_for('main.contact'))
        else:
            flash('Error sending message. Please try again.', 'danger')
    
    return render_template('contact.html')
