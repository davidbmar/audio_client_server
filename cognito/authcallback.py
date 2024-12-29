# authcallback.py
import boto3
import json
import logging
import os
import requests
import secrets

from authlib.integrations.flask_client import OAuth
from datetime import datetime, timedelta
from flask_session import Session
from flask import (
    Flask, redirect, url_for, session, request, 
    render_template_string, Response, make_response, jsonify
)
from functools import wraps
from s3_manager import get_secrets, create_s3_client, get_input_bucket
from typing import Optional, Callable, Dict, Any
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import HTTPException


# Configuration for internal service URL  SECURITY WARNING - note this should be an internal service only, fix the apache2 conf.
# This could be moved to environment variables or config file
PRESIGNED_URL_SERVICE = os.environ.get('PRESIGNED_URL_SERVICE', 'http://localhost:8000')
REGION = 'us-east-2'

# Update logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sanitize_token_for_logging(token: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a copy of the token safe for logging by removing sensitive fields
    """
    sensitive_fields = {'access_token', 'refresh_token', 'id_token'}
    return {k: v for k, v in token.items() if k not in sensitive_fields}


def validate_cognito_token(token):
    """
    Validates the Cognito JWT token and returns the claims if valid
    Raises ValueError if invalid
    """
    try:
        # Decode and verify the token
        # Note: In production, you'd want to verify against Cognito's public keys
        claims = jwt.decode(token, verify=False)
        return claims
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")



def debug_log_session():
    """Log current session information"""
    user_info = session.get('user', {})
    logger.debug("Current session info:")
    logger.debug(json.dumps(user_info, indent=2))
    
    if user_info:
        # Get S3 path that would be used
        user_id = user_info.get('sub', '')
        user_type = user_info.get('user_type', 'customer')
        s3_path = f"users/{user_type}/{user_id}/"
        logger.debug(f"S3 path for user: {s3_path}")
        
        # Get S3 bucket information
        try:
            input_bucket = get_input_bucket()
            logger.debug(f"S3 bucket: {input_bucket}")
            logger.debug(f"Full S3 path: s3://{input_bucket}/{s3_path}")
        except Exception as e:
            logger.error(f"Error getting S3 information: {e}")

def extract_provider_from_token(userinfo: dict) -> str:
    """
    Extract the authentication provider from the userinfo.
    Returns 'cognito', 'google', etc.
    """
    try:
        issuer = userinfo.get('iss', '')
        if 'cognito-idp' in issuer:
            return 'cognito'
        elif 'accounts.google.com' in issuer:
            return 'google'
        elif 'github.com' in issuer:
            return 'github'
        else:
            logger.warning(f"Unknown provider issuer: {issuer}")
            return 'unknown'
    except Exception as e:
        logger.error(f"Error extracting provider: {str(e)}")
        return 'unknown'

def login_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user')
        if user is None:
            logger.warning("Unauthenticated access attempt")
            debug_log_session()
            return redirect(url_for('login'))
        
        try:
            authenticated_at = datetime.fromisoformat(user.get('authenticated_at', ''))
            if datetime.utcnow() - authenticated_at > timedelta(hours=12):
                logger.info("Session expired, redirecting to login")
                session.clear()
                return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error validating session expiration: {str(e)}")
            session.clear()
            return redirect(url_for('login'))
            
        return f(*args, **kwargs)
    return decorated_function

# Initialize Flask app with security configurations
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Update app.config for session
app.config.update(
    SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', secrets.token_urlsafe(32)),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_TYPE='filesystem',  # Replace with 'redis' for production
    SESSION_PERMANENT=True
)
Session(app)

# Initialize OAuth
oauth = OAuth(app)
oauth.register(
    name='oidc',
    client_id=os.environ.get('COGNITO_CLIENT_ID', '3ko89b532mtv90e3242ni1fno4'),
    client_secret=os.environ.get('COGNITO_CLIENT_SECRET', '14jan2ru58v1f5houc2sbdscm21v3d3g7ovrkua2sbedintm069l'),
    server_metadata_url='https://cognito-idp.us-east-2.amazonaws.com/us-east-2_cBWwWPDou/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email phone',
        'code_challenge_method': 'S256'
    }
)

def set_security_headers(response: Response) -> Response:
    """Add security headers to all responses"""
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

@app.after_request
def after_request(response: Response) -> Response:
    """Global handler to set security headers"""
    return set_security_headers(response)

@app.route('/home')
def index():
    user = session.get('user')
    response = make_response(render_template_string('''
        <h1>Welcome to My App</h1>
        {% if user %}
            <p>Hello, {{ user.email }} ({{ user.user_type }})! <a href="/logout">Logout</a></p>
        {% else %}
            <p>Welcome! Please <a href="/login">Login</a></p>
        {% endif %}
        <nav>
            <ul>
                <li><a href="/public">Public Page</a></li>
                <li><a href="/dashboard">Dashboard (Protected)</a></li>
            </ul>
        </nav>
    ''', user=user))
    return response

@app.route('/public')
def public():
    response = make_response(render_template_string('''
        <h1>Public Page</h1>
        <p>This content is visible to everyone!</p>
        <p><a href="/">Back to Home</a></p>
    '''))
    return response

@app.route('/dashboard')
@login_required
def dashboard():
    user = session.get('user')
    s3_path = f"users/{user['user_type']}/{user['provider']}/{user['sub']}/"
    
    response = make_response(render_template_string('''
        <h1>Protected Dashboard</h1>
        <h2>Welcome, {{ user.email }}!</h2>
        <h3>Your Profile Information:</h3>
        <ul>
            {% for key, value in user.items() %}
                <li><strong>{{ key }}:</strong> {{ value }}</li>
            {% endfor %}
        </ul>
        <h3>Your S3 Information:</h3>
        <ul>
            <li><strong>User ID:</strong> {{ user.sub }}</li>
            <li><strong>User Type:</strong> {{ user.user_type }}</li>
            <li><strong>Provider:</strong> {{ user.provider }}</li>
            <li><strong>S3 Path:</strong> {{ s3_path }}</li>
        </ul>
        <p>
            <a href="/">Back to Home</a> | 
            <a href="/logout">Logout</a>
        </p>
    ''', user=user, s3_path=s3_path))
    return response

@app.route('/login')
def login():
    try:
        csrf_token = secrets.token_urlsafe(32)
        session['csrf_token'] = csrf_token
        redirect_uri = url_for('callback', _external=True)
        logger.debug(f"Generated redirect URI: {redirect_uri}")
        return oauth.oidc.authorize_redirect(redirect_uri)
    except Exception as e:
        logger.error(f"Error during login redirect: {str(e)}", exc_info=True)
        return redirect(url_for('index'))

@app.route('/auth/callback')
def callback():
    try:
        logger.info("Starting authentication callback...")
        token = oauth.oidc.authorize_access_token()
        logger.debug(f"Retrieved token: {sanitize_token_for_logging(token)}")
        
        userinfo = token.get('userinfo', {})
        logger.debug(f"Retrieved userinfo: {userinfo}")
        
        if not userinfo or not userinfo.get('sub'):
            logger.error("Failed to get valid user info from OAuth provider")
            return redirect(url_for('login'))

        # Extract provider from token
        provider = extract_provider_from_token(userinfo)
        logger.debug(f"Authentication provider: {provider}")
        
        # Clear and create new session
        session.clear()
        session.permanent = True
        session['_id'] = secrets.token_urlsafe(32)
        
        session['user'] = {
            'sub': userinfo['sub'],
            'email': userinfo.get('email', ''),
            'user_type': 'customer',  # Default type
            'provider': provider,
            'authenticated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"User {userinfo.get('email')} authenticated successfully via {provider}")
        debug_log_session()
        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error during authentication callback: {str(e)}", exc_info=True)
        session.clear()
        return render_template_string('''
            <h1>Something went wrong</h1>
            <p>{{ error }}</p>
        ''', error=str(e))

@app.route('/auth/audio-upload', methods=['POST'])
def handle_audio_upload_request():
    """
    Handles requests for audio upload URLs
    """
    try:
        # Validate required headers
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing Authorization header'}), 401
            
        # Split header and validate format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid Authorization header format'}), 401
            
        token = parts[1]
        
        # Validate Content-Type
        if request.headers.get('Content-Type') != 'application/x-amz-json-1.1':
            return jsonify({'error': 'Invalid Content-Type'}), 400

        try:
            claims = validate_cognito_token(token)
        except ValueError as e:
            return jsonify({'error': str(e)}), 401

        # Generate timestamp for the file
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S-%f')
        
        # Construct the path
        user_type = claims.get('custom:user_type', 'default')
        provider = claims.get('custom:provider', 'default')
        user_sub = claims['sub']
        file_path = f"users/{user_type}/{provider}/{user_sub}/{timestamp}.webm"

        # Forward request to PresignedURL service
        presigned_url_request = {
            'bucket': '2024-09-23-audiotranscribe-input-bucket',
            'key': file_path,
            'content_type': 'audio/webm'
        }

        response = requests.post(
            PRESIGNED_URL_SERVICE,
            json=presigned_url_request,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            return jsonify({'error': 'Failed to generate upload URL'}), 502

        presigned_data = response.json()
        
        return jsonify({
            'upload_url': presigned_data['url'],
            'key': file_path
        })

    except HTTPException as e:
        return jsonify({'error': str(e)}), e.code
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/logout')
def logout():
    try:
        # Clear session
        session.clear()
        
        # Cognito logout URL construction
        cognito_domain = "https://davidbmar.auth.us-east-2.amazoncognito.com"
        client_id = os.environ.get('COGNITO_CLIENT_ID', '3ko89b532mtv90e3242ni1fno4')
        logout_uri = "https://www.davidbmar.com"

        logout_url = (
            f"{cognito_domain}/logout?"
            f"client_id={client_id}&"
            f"logout_uri={logout_uri}"
        )
        
        logger.info("User logged out successfully")
        return redirect(logout_url)
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return redirect(url_for('index'))

@app.route('/get-presigned-url')
@login_required
def get_presigned_url():
    try:
        user = session.get('user')
        if not user:
            logger.error("No user found in session")
            return jsonify({'error': 'User not authenticated'}), 401

        # Log attempt for debugging
        logger.info(f"Presigned URL request from user: {user.get('email')}")
        
        # For initial test, just return user info
        return jsonify({
            'message': 'Test endpoint working',
            'user_id': user.get('sub'),
            'email': user.get('email')
        })

    except Exception as e:
        logger.error(f"Error in get-presigned-url endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error: {request.url}")
    return make_response(render_template_string('''
        <h1>Page Not Found</h1>
        <p>The requested page could not be found.</p>
        <p><a href="/">Return to Home</a></p>
    '''), 404)

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return make_response(render_template_string('''
        <h1>Internal Server Error</h1>
        <p>An unexpected error has occurred.</p>
        <p><a href="/">Return to Home</a></p>
    '''), 500)

if __name__ == '__main__':
    # Ensure debug mode is off in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', debug=debug_mode)
