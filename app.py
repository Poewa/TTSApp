from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from openai import AzureOpenAI
import os
from pathlib import Path
import uuid
import time
import requests
import subprocess
import re
import html
import json
import logging
from functools import wraps
from typing import Optional, Dict, List, Any, Union
from auth import get_user, get_user_by_username, create_user, create_azure_ad_user, User
import msal
from urllib.parse import urlparse, urljoin # Added for security check


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# --- Configuration Loading ---

# Security configurations
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
app.config['REQUIRE_AUTHENTICATION'] = os.getenv('REQUIRE_AUTHENTICATION', 'true').lower() == 'true'
app.config['ALLOW_REGISTRATION'] = os.getenv('ALLOW_REGISTRATION', 'true').lower() == 'true'

# Azure AD configuration
app.config['AZURE_AD_CLIENT_ID'] = os.getenv('AZURE_AD_CLIENT_ID')
app.config['AZURE_AD_CLIENT_SECRET'] = os.getenv('AZURE_AD_CLIENT_SECRET')
app.config['AZURE_AD_TENANT_ID'] = os.getenv('AZURE_AD_TENANT_ID')
app.config['AZURE_AD_REDIRECT_PATH'] = '/login/azure/callback'

# Model and limits configuration
app.config['AZURE_OPENAI_MODEL'] = os.getenv('AZURE_OPENAI_MODEL', 'tts-hd')
app.config['AZURE_OPENAI_TIMEOUT'] = int(os.getenv('AZURE_OPENAI_TIMEOUT', 30))
app.config['MAX_TEXT_LENGTH'] = int(os.getenv('MAX_TEXT_LENGTH', 10000))
app.config['MAX_FILE_AGE_SECONDS'] = int(os.getenv('MAX_FILE_AGE_SECONDS', 3600))
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
app.config['JSON_SORT_KEYS'] = False

# --- Default Voice Lists ---
DEFAULT_SPEECH_SERVICE_VOICES = [
    {'name': 'da-DK-ChristelNeural', 'displayName': 'Christel (DK Female)', 'language': 'da-DK'},
    {'name': 'da-DK-JeppeNeural', 'displayName': 'Jeppe (DK Male)', 'language': 'da-DK'},
    {'name': 'en-GB-SoniaNeural', 'displayName': 'Sonia (UK Female)', 'language': 'en-GB'},
    {'name': 'en-GB-RyanNeural', 'displayName': 'Ryan (UK Male)', 'language': 'en-GB'},
]

DEFAULT_OPENAI_VOICES = [
    {'name': 'alloy', 'displayName': 'Alloy', 'language': 'en-US'},
    {'name': 'echo', 'displayName': 'Echo', 'language': 'en-US'},
    {'name': 'fable', 'displayName': 'Fable', 'language': 'en-US'},
    {'name': 'onyx', 'displayName': 'Onyx', 'language': 'en-US'},
    {'name': 'nova', 'displayName': 'Nova', 'language': 'en-US'},
    {'name': 'shimmer', 'displayName': 'Shimmer', 'language': 'en-US'},
]

# --- Load Voices from Environment or Use Defaults ---
try:
    speech_service_voices_json = os.getenv('SPEECH_SERVICE_VOICES')
    app.config['SPEECH_SERVICE_VOICES'] = json.loads(speech_service_voices_json) if speech_service_voices_json else DEFAULT_SPEECH_SERVICE_VOICES
except json.JSONDecodeError:
    logger.warning("Invalid JSON in SPEECH_SERVICE_VOICES env var. Using default voices.")
    app.config['SPEECH_SERVICE_VOICES'] = DEFAULT_SPEECH_SERVICE_VOICES

try:
    openai_voices_json = os.getenv('OPENAI_VOICES')
    app.config['OPENAI_VOICES'] = json.loads(openai_voices_json) if openai_voices_json else DEFAULT_OPENAI_VOICES
except json.JSONDecodeError:
    logger.warning("Invalid JSON in OPENAI_VOICES env var. Using default voices.")
    app.config['OPENAI_VOICES'] = DEFAULT_OPENAI_VOICES


# Initialize Flask-Login only if authentication is required
if app.config['REQUIRE_AUTHENTICATION']:
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        return get_user(user_id)

# Conditional login requirement decorator
def conditional_login_required(f):
    """Require login only if REQUIRE_AUTHENTICATION is enabled"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if app.config['REQUIRE_AUTHENTICATION']:
            return login_required(f)(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated_function

def get_msal_app() -> Optional[msal.ConfidentialClientApplication]:
    """Create MSAL confidential client application"""
    if not app.config['AZURE_AD_CLIENT_ID']:
        return None

    authority = f"https://login.microsoftonline.com/{app.config['AZURE_AD_TENANT_ID']}"
    return msal.ConfidentialClientApplication(
        app.config['AZURE_AD_CLIENT_ID'],
        authority=authority,
        client_credential=app.config['AZURE_AD_CLIENT_SECRET']
    )

# Security helper function
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

# Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

# Configure Azure OpenAI (optional for demo)
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

client: Optional[AzureOpenAI] = None
if AZURE_API_KEY and AZURE_ENDPOINT:
    client = AzureOpenAI(
        api_key=AZURE_API_KEY,
        api_version=AZURE_API_VERSION,
        azure_endpoint=AZURE_ENDPOINT,
        timeout=app.config['AZURE_OPENAI_TIMEOUT'],
    )
    logger.info("✅ Azure OpenAI client configured successfully")
else:
    logger.warning("⚠️  Running in DEMO mode - Azure OpenAI credentials not configured")
    logger.warning("   Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT to enable TTS")

# Configure Azure Speech Service
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

if AZURE_SPEECH_KEY and AZURE_SPEECH_REGION:
    logger.info(f"✅ Azure Speech Service configured with region: {AZURE_SPEECH_REGION}")
else:
    logger.warning("⚠️  Azure Speech Service not configured")
    logger.warning("   Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION to enable Speech Service")

# Create directory for audio files inside data directory
DATA_DIR = Path("data")
AUDIO_DIR = DATA_DIR / "audio"
# Create directories with exist_ok to handle volume mount permissions
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except (PermissionError, FileExistsError):
    # Directory might already exist from volume mount
    pass

try:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
except (PermissionError, FileExistsError):
    # If we can't create it, check if it exists
    if not AUDIO_DIR.exists():
        logger.warning(f"⚠️  Warning: Unable to create audio directory at {AUDIO_DIR}")
        logger.warning(f"   Audio files will not be saved. Check directory permissions.")
    pass

def cleanup_old_audio_files() -> int:
    """Remove audio files older than MAX_FILE_AGE_SECONDS"""
    try:
        current_time = time.time()
        deleted_count = 0

        # Remove both mp3 and wav files older than the configured age
        for pattern in ("*.mp3", "*.wav"):
            for audio_file in AUDIO_DIR.glob(pattern):
                file_age = current_time - audio_file.stat().st_mtime
                if file_age > app.config['MAX_FILE_AGE_SECONDS']:
                    try:
                        audio_file.unlink()
                        deleted_count += 1
                    except Exception:
                        pass

        if deleted_count > 0:
            logger.info(f"🧹 Cleaned up {deleted_count} old audio file(s)")
        return deleted_count
    except Exception as e:
        logger.error(f"⚠️  Error during audio cleanup: {e}")
        return 0

# Run cleanup on startup
cleanup_old_audio_files()

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If authentication is disabled, redirect to index
    if not app.config['REQUIRE_AUTHENTICATION']:
        return redirect(url_for('index'))

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Indtast venligst både brugernavn og adgangskode', 'error')
            return render_template('login.html',
                                 allow_registration=app.config['ALLOW_REGISTRATION'],
                                 azure_ad_enabled=bool(app.config['AZURE_AD_CLIENT_ID']))

        user = get_user_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash('Ugyldigt brugernavn eller adgangskode', 'error')

    return render_template('login.html',
                         allow_registration=app.config['ALLOW_REGISTRATION'],
                         azure_ad_enabled=bool(app.config['AZURE_AD_CLIENT_ID']))

@app.route('/login/azure')
def login_azure():
    """Initiate Azure AD OAuth flow"""
    if not app.config['REQUIRE_AUTHENTICATION']:
        return redirect(url_for('index'))

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    msal_app = get_msal_app()
    if not msal_app:
        flash('Azure AD ikke konfigureret', 'error')
        return redirect(url_for('login'))

    # Generate authorization URL
    redirect_uri = url_for('login_azure_callback', _external=True)
    auth_url = msal_app.get_authorization_request_url(
        scopes=["User.Read"],
        redirect_uri=redirect_uri
    )

    return redirect(auth_url)

@app.route('/login/azure/callback')
def login_azure_callback():
    """Handle Azure AD OAuth callback"""
    if not app.config['REQUIRE_AUTHENTICATION']:
        return redirect(url_for('index'))

    msal_app = get_msal_app()
    if not msal_app:
        flash('Azure AD ikke konfigureret', 'error')
        return redirect(url_for('login'))

    # Get authorization code from query parameters
    code = request.args.get('code')
    if not code:
        error = request.args.get('error_description', 'Ukendt fejl')
        flash(f'Azure AD login fejlede: {error}', 'error')
        return redirect(url_for('login'))

    try:
        # Exchange code for token
        redirect_uri = url_for('login_azure_callback', _external=True)
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=["User.Read"],
            redirect_uri=redirect_uri
        )

        if "error" in result:
            flash(f'Azure AD login fejlede: {result.get("error_description")}', 'error')
            return redirect(url_for('login'))

        # Get user info from Microsoft Graph
        access_token = result['access_token']
        graph_response = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if graph_response.status_code != 200:
            flash('Kunne ikke hente brugeroplysninger fra Azure AD', 'error')
            return redirect(url_for('login'))

        user_info = graph_response.json()
        email = user_info.get('mail') or user_info.get('userPrincipalName')
        display_name = user_info.get('displayName', email.split('@')[0])

        # Create or get Azure AD user
        user, error = create_azure_ad_user(email, display_name)
        if error:
            flash(f'Kunne ikke oprette bruger: {error}', 'error')
            return redirect(url_for('login'))

        # Log user in
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or not is_safe_url(next_page):
            next_page = url_for('index')
        return redirect(next_page)

    except Exception as e:
        flash(f'Azure AD login fejlede: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    logger.info(f"🔍 REGISTER route - ALLOW_REGISTRATION config: {app.config['ALLOW_REGISTRATION']}")

    # If authentication is disabled, redirect to index
    if not app.config['REQUIRE_AUTHENTICATION']:
        return redirect(url_for('index'))

    if not app.config['ALLOW_REGISTRATION']:
        return redirect(url_for('login'))

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password or not confirm_password:
            flash('Alle felter skal udfyldes', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Adgangskoderne matcher ikke', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Adgangskoden skal være mindst 6 tegn lang', 'error')
            return render_template('register.html')

        user, error = create_user(username, password)
        if error:
            flash(error, 'error')
            return render_template('register.html')

        flash('Registrering gennemført! Log venligst ind.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@conditional_login_required
def logout():
    if app.config['REQUIRE_AUTHENTICATION']:
        logout_user()
        return redirect(url_for('login'))
    return redirect(url_for('index'))

@app.route('/')
@conditional_login_required
def index():
    username = current_user.username if (app.config['REQUIRE_AUTHENTICATION'] and current_user.is_authenticated) else None
    return render_template('index.html', username=username, require_auth=app.config['REQUIRE_AUTHENTICATION'])

@app.route('/get-voices', methods=['GET'])
@conditional_login_required
def get_voices():
    """Get available voices for the selected service"""
    try:
        service = request.args.get('service', 'openai')
        if service == 'speech':
            voices = app.config['SPEECH_SERVICE_VOICES']
        else:
            voices = app.config['OPENAI_VOICES']
        return jsonify({'voices': voices})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-speech', methods=['POST'])
@conditional_login_required
@limiter.limit("5 per minute")  # Rate limit: 5 requests per minute per user/IP
def generate_speech():
    try:
        data = request.json
        text = data.get('text', '')
        voice = data.get('voice', 'alloy')
        service = data.get('service', 'openai')
        speed = data.get('speed', 1.0)

        logger.info(f"📝 Request received - Service: {service}, Voice: {voice}, Speed: {speed}x, Text length: {len(text)}")

        # Input validation
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        max_len = app.config['MAX_TEXT_LENGTH']
        if len(text) > max_len:
            return jsonify({'error': f'Text too long. Maximum {max_len} characters allowed.'}), 400

        if service not in ['openai', 'speech']:
            return jsonify({'error': 'Invalid service selection'}), 400

        if not (0.25 <= speed <= 4.0):
            return jsonify({'error': 'Invalid speed value. Must be between 0.25 and 4.0'}), 400

        filename = f"{uuid.uuid4()}.mp3"
        filepath = AUDIO_DIR / filename

        if service == 'speech':
            if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
                return jsonify({'error': 'Azure Speech Service is not configured.'}), 503

            speech_url = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
            headers = {
                'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'audio-24khz-96kbitrate-mono-mp3',
                'User-Agent': 'TTSApp'
            }
            rate_percent = max(-50, min(100, int((speed - 1.0) * 100)))
            rate_str = f"+{rate_percent}%" if rate_percent > 0 else f"{rate_percent}%"
            safe_text = html.escape(text)
            ssml = f"""<speak version='1.0' xml:lang='en-US'>
                <voice xml:lang='en-US' name='{voice}'><prosody rate='{rate_str}'>{safe_text}</prosody></voice>
            </speak>"""

            try:
                response = requests.post(speech_url, headers=headers, data=ssml.encode('utf-8'), timeout=30)
                if response.status_code == 200:
                    with open(filepath, 'wb') as audio_file:
                        audio_file.write(response.content)
                    logger.info(f"✅ Speech synthesized with Azure Speech Service (voice: {voice})")
                else:
                    error_msg = f"Azure Speech Service error: {response.status_code} - {response.text}"
                    logger.error(f"❌ {error_msg}")
                    return jsonify({'error': error_msg}), 500
            except Exception as e:
                error_msg = f"Failed to connect to Azure Speech Service: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return jsonify({'error': error_msg}), 500
        else:
            if not client:
                return jsonify({'error': 'Azure OpenAI is not configured.'}), 503

            response = client.audio.speech.create(
                model=app.config['AZURE_OPENAI_MODEL'],
                voice=voice,
                input=text,
                speed=speed
            )
            response.stream_to_file(str(filepath))
            logger.info(f"✅ Speech synthesized with OpenAI TTS (voice: {voice})")

        cleanup_old_audio_files()

        return jsonify({'success': True, 'audio_url': f'/audio/{filename}', 'filename': filename})
    except Exception as e:
        logger.error(f"Error in generate_speech: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
@conditional_login_required
def serve_audio(filename):
    """Serve audio files from data directory"""
    try:
        if not re.match(r'^[a-f0-9\-]+\.mp3$', filename):
            return jsonify({'error': 'Invalid filename'}), 400

        filepath = AUDIO_DIR / filename
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404

        return send_file(filepath, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
@conditional_login_required
def download_file(filename):
    try:
        if not re.match(r'^[a-f0-9\-]+\.mp3$', filename):
            return jsonify({'error': 'Invalid filename'}), 400

        filepath = AUDIO_DIR / filename
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404

        fmt = request.args.get('format', 'mp3').lower()
        if fmt == 'mp3':
            return send_file(filepath, as_attachment=True)
        elif fmt == 'wav':
            stem = filepath.stem
            wav_path = AUDIO_DIR / f"{stem}.wav"
            if not wav_path.exists():
                try:
                    subprocess.run(
                        ['ffmpeg', '-y', '-i', str(filepath), '-ar', '24000', '-ac', '1', str(wav_path)],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                except subprocess.CalledProcessError:
                    return jsonify({'error': 'Failed to convert to WAV'}), 500
            return send_file(wav_path, as_attachment=True)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)