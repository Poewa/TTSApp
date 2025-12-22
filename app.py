from flask import Flask, render_template, request, jsonify, send_file
from openai import AzureOpenAI
import os
from pathlib import Path
import uuid
import time
import requests

app = Flask(__name__)

# Security configurations
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
app.config['JSON_SORT_KEYS'] = False

# Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
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

        for audio_file in AUDIO_DIR.glob("*.mp3"):
            file_age = current_time - audio_file.stat().st_mtime
            if file_age > MAX_FILE_AGE_SECONDS:
                audio_file.unlink()
                deleted_count += 1

        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} old audio file(s)")
        return deleted_count
    except Exception as e:
        print(f"⚠️  Error during audio cleanup: {e}")
        return 0

# Run cleanup on startup
cleanup_old_audio_files()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-voices', methods=['GET'])
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
def generate_speech():
    try:
        data = request.json
        text = data.get('text', '')
        voice = data.get('voice', 'alloy')
        service = data.get('service', 'openai')  # 'openai' or 'speech'

        print(f"📝 Request received - Service: {service}, Voice: {voice}, Text length: {len(text)}")

        if not text:
            return jsonify({'error': 'No text provided'}), 400

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

            # Prepare headers
            headers = {
                'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'audio-16khz-32kbitrate-mono-mp3',
                'User-Agent': 'TTSApp'
            }

            # Prepare SSML body
            ssml = f"""<speak version='1.0' xml:lang='en-US'>
                <voice xml:lang='en-US' name='{voice}'>
                    {text}
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

            # Call Azure OpenAI TTS API
            response = client.audio.speech.create(
                model="tts-hd",  # Your deployment name
                voice=voice,
                input=text
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
def download_file(filename):
    try:
        filepath = AUDIO_DIR / filename
        if filepath.exists():
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Only use debug mode in development
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
