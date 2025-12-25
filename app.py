from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from openai import AzureOpenAI
import os
from pathlib import Path
import uuid
import time
import requests
import subprocess
import re
import html
from auth import get_user, get_user_by_username, create_user

app = Flask(__name__)

# Security configurations
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)

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

client = None
if AZURE_API_KEY and AZURE_ENDPOINT:
    client = AzureOpenAI(
        api_key=AZURE_API_KEY,
        api_version=AZURE_API_VERSION,
        azure_endpoint=AZURE_ENDPOINT
    )
    print("✅ Azure OpenAI client configured successfully")
else:
    print("⚠️  Running in DEMO mode - Azure OpenAI credentials not configured")
    print("   Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT to enable TTS")

# Configure Azure Speech Service
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

if AZURE_SPEECH_KEY and AZURE_SPEECH_REGION:
    print(f"✅ Azure Speech Service configured with region: {AZURE_SPEECH_REGION}")
else:
    print("⚠️  Azure Speech Service not configured")
    print("   Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION to enable Speech Service")

# Create directory for audio files
AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Audio file cleanup settings
MAX_FILE_AGE_SECONDS = 3600  # 1 hour

def cleanup_old_audio_files():
    """Remove audio files older than MAX_FILE_AGE_SECONDS"""
    try:
        current_time = time.time()
        deleted_count = 0

        # Remove both mp3 and wav files older than the configured age
        for pattern in ("*.mp3", "*.wav"):
            for audio_file in AUDIO_DIR.glob(pattern):
                file_age = current_time - audio_file.stat().st_mtime
                if file_age > MAX_FILE_AGE_SECONDS:
                    try:
                        audio_file.unlink()
                        deleted_count += 1
                    except Exception:
                        pass

        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} old audio file(s)")
        return deleted_count
    except Exception as e:
        print(f"⚠️  Error during audio cleanup: {e}")
        return 0

# Run cleanup on startup
cleanup_old_audio_files()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password', 'error')
            return render_template('login.html')
        
        user = get_user_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    print(f"🔍 REGISTER route called - Method: {request.method}")
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        print(f"🔍 Registration attempt - Username: {username}")
        
        if not username or not password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        user, error = create_user(username, password)
        if error:
            flash(error, 'error')
            return render_template('register.html')
        
        print(f"✅ User {username} registered successfully")
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', username=current_user.username)

@app.route('/get-voices', methods=['GET'])
@login_required
def get_voices():
    """Get available voices for the selected service"""
    try:
        service = request.args.get('service', 'openai')

        if service == 'speech':
            # Azure Speech Service voices - Danish and UK English only
            voices = [
                # Danish voices (default)
                {'name': 'da-DK-ChristelNeural', 'displayName': 'Christel (DK Female)', 'language': 'da-DK'},
                {'name': 'da-DK-JeppeNeural', 'displayName': 'Jeppe (DK Male)', 'language': 'da-DK'},
                # UK English voices
                {'name': 'en-GB-SoniaNeural', 'displayName': 'Sonia (UK Female)', 'language': 'en-GB'},
                {'name': 'en-GB-RyanNeural', 'displayName': 'Ryan (UK Male)', 'language': 'en-GB'},
            ]
        else:
            # Azure OpenAI TTS voices
            voices = [
                {'name': 'alloy', 'displayName': 'Alloy', 'language': 'en-US'},
                {'name': 'echo', 'displayName': 'Echo', 'language': 'en-US'},
                {'name': 'fable', 'displayName': 'Fable', 'language': 'en-US'},
                {'name': 'onyx', 'displayName': 'Onyx', 'language': 'en-US'},
                {'name': 'nova', 'displayName': 'Nova', 'language': 'en-US'},
                {'name': 'shimmer', 'displayName': 'Shimmer', 'language': 'en-US'},
            ]

        return jsonify({'voices': voices})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-speech', methods=['POST'])
@login_required
def generate_speech():
    try:
        data = request.json
        text = data.get('text', '')
        voice = data.get('voice', 'alloy')
        service = data.get('service', 'openai')  # 'openai' or 'speech'
        speed = data.get('speed', 1.0)  # Speed multiplier (0.5 to 2.0)

        print(f"📝 Request received - Service: {service}, Voice: {voice}, Speed: {speed}x, Text length: {len(text)}")

        # Input validation
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        if len(text) > 10000:  # Reasonable limit for TTS
            return jsonify({'error': 'Text too long. Maximum 10,000 characters allowed.'}), 400

        # Validate service selection
        if service not in ['openai', 'speech']:
            return jsonify({'error': 'Invalid service selection'}), 400

        # Validate speed range
        if not (0.25 <= speed <= 4.0):
            return jsonify({'error': 'Invalid speed value. Must be between 0.25 and 4.0'}), 400

        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = AUDIO_DIR / filename

        if service == 'speech':
            # Use Azure Speech Service REST API
            if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
                return jsonify({
                    'error': 'Azure Speech Service is not configured. Please set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in your .env file.'
                }), 503

            # Construct the REST API endpoint
            speech_url = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

            # Prepare headers with higher quality audio format
            headers = {
                'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'audio-24khz-96kbitrate-mono-mp3',  # Higher quality
                'User-Agent': 'TTSApp'
            }

            # Prepare SSML body with speed control
            # Convert speed (0.5-2.0) to percentage for SSML rate
            # Clamp to safe range to avoid artifacts
            rate_percent = max(-50, min(100, int((speed - 1.0) * 100)))
            rate_str = f"+{rate_percent}%" if rate_percent > 0 else f"{rate_percent}%"

            # Escape text to prevent SSML injection
            safe_text = html.escape(text)

            ssml = f"""<speak version='1.0' xml:lang='en-US'>
                <voice xml:lang='en-US' name='{voice}'>
                    <prosody rate='{rate_str}'>
                        {safe_text}
                    </prosody>
                </voice>
            </speak>"""

            try:
                # Make request to Azure Speech Service
                response = requests.post(speech_url, headers=headers, data=ssml.encode('utf-8'), timeout=30)

                if response.status_code == 200:
                    # Save the audio file
                    with open(filepath, 'wb') as audio_file:
                        audio_file.write(response.content)
                    print(f"✅ Speech synthesized successfully with Azure Speech Service (voice: {voice})")
                else:
                    error_msg = f"Azure Speech Service error: {response.status_code} - {response.text}"
                    print(f"❌ {error_msg}")
                    return jsonify({'error': error_msg}), 500
            except Exception as e:
                error_msg = f"Failed to connect to Azure Speech Service: {str(e)}"
                print(f"❌ {error_msg}")
                return jsonify({'error': error_msg}), 500
        else:
            # Use Azure OpenAI TTS
            if not client:
                return jsonify({
                    'error': 'Azure OpenAI is not configured. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in your .env file to enable text-to-speech functionality.'
                }), 503

            # Call Azure OpenAI TTS API with speed control
            response = client.audio.speech.create(
                model="tts-hd",  # Your deployment name
                voice=voice,
                input=text,
                speed=speed
            )

            # Save the audio file
            response.stream_to_file(str(filepath))
            print(f"✅ Speech synthesized successfully with OpenAI TTS (voice: {voice})")

        # Cleanup old files after generating new one
        cleanup_old_audio_files()

        return jsonify({
            'success': True,
            'audio_url': f'/static/audio/{filename}',
            'filename': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    try:
        # Validate filename (we only expect generated UUID filenames like <uuid>.mp3)
        if not re.match(r'^[a-f0-9\-]+\.mp3$', filename):
            return jsonify({'error': 'Invalid filename'}), 400

        filepath = AUDIO_DIR / filename
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404

        # Optional format query parameter: ?format=wav or ?format=mp3
        fmt = request.args.get('format', 'mp3').lower()
        if fmt == 'mp3':
            return send_file(filepath, as_attachment=True)
        elif fmt == 'wav':
            # Check if WAV already exists (cache)
            stem = filepath.stem
            wav_path = AUDIO_DIR / f"{stem}.wav"
            if not wav_path.exists():
                # Convert mp3 -> wav using ffmpeg
                try:
                    # Use a safe, fixed ffmpeg command. Overwrite if exists (-y).
                    subprocess.run([
                        'ffmpeg', '-y', '-i', str(filepath),
                        '-ar', '24000',  # sample rate 24kHz
                        '-ac', '1',      # mono
                        str(wav_path)
                    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError as e:
                    return jsonify({'error': 'Failed to convert to WAV'}), 500

            return send_file(wav_path, as_attachment=True)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Only use debug mode in development
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
