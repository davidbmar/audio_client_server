from flask import Flask, redirect, url_for, session, request, render_template_string
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
import os

# Decorator definition first
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user')
        if user is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.secret_key = 'your-secure-secret-key-here'
oauth = OAuth(app)

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

oauth.register(
    name='oidc',
    client_id='3ko89b532mtv90e3242ni1fno4',
    client_secret='14jan2ru58v1f5houc2sbdscm21v3d3g7ovrkua2sbedintm069l',
    server_metadata_url='https://cognito-idp.us-east-2.amazonaws.com/us-east-2_cBWwWPDou/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email phone',
        'code_challenge_method': 'S256'
    }
)

# Public page - anyone can access
@app.route('/')
def index():
    user = session.get('user')
    return render_template_string('''
        <h1>Welcome to My App</h1>
        {% if user %}
            <p>Hello, {{ user.email }}! <a href="/logout">Logout</a></p>
        {% else %}
            <p>Welcome! Please <a href="/login">Login</a></p>
        {% endif %}
        <nav>
            <ul>
                <li><a href="/public">Public Page</a></li>
                <li><a href="/dashboard">Dashboard (Protected)</a></li>
            </ul>
        </nav>
    ''', user=user)

# Another public page
@app.route('/public')
def public():
    return render_template_string('''
        <h1>Public Page</h1>
        <p>This content is visible to everyone!</p>
        <p><a href="/">Back to Home</a></p>
    ''')

# Protected page - only authenticated users can access
@app.route('/dashboard')
@login_required
def dashboard():
    user = session.get('user')
    return render_template_string('''
        <h1>Protected Dashboard</h1>
        <h2>Welcome, {{ user.email }}!</h2>
        <h3>Your Profile Information:</h3>
        <ul>
            {% for key, value in user.items() %}
                <li><strong>{{ key }}:</strong> {{ value }}</li>
            {% endfor %}
        </ul>
        <p>
            <a href="/">Back to Home</a> | 
            <a href="/logout">Logout</a>
        </p>
    ''', user=user)


@app.route('/login')
def login():
    redirect_uri = url_for('callback', _external=True)
    return oauth.oidc.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def callback():
    try:
        token = oauth.oidc.authorize_access_token()
        user = token.get('userinfo')
        if user:
            session['user'] = user
            return redirect(url_for('index'))
        else:
            return 'Failed to get user info', 400
    except Exception as e:
        print(f"Error during callback: {str(e)}")
        session.clear()
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()

    cognito_domain = "https://davidbmar.auth.us-east-2.amazoncognito.com"
    client_id = "3ko89b532mtv90e3242ni1fno4"
    logout_uri = "https://www.davidbmar.com"  # Match this with Cognito's allowed sign-out URL

    return redirect(
        f"{cognito_domain}/logout?client_id={client_id}&logout_uri={logout_uri}"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
