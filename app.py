from flask import Flask, render_template, request, jsonify, send_file
from openai import AzureOpenAI
import os
from pathlib import Path
import uuid

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

# Create directory for audio files
AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-speech', methods=['POST'])
def generate_speech():
    try:
        data = request.json
        text = data.get('text', '')
        voice = data.get('voice', 'alloy')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Check if Azure OpenAI is configured
        if not client:
            return jsonify({
                'error': 'Azure OpenAI is not configured. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in your .env file to enable text-to-speech functionality.'
            }), 503

        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = AUDIO_DIR / filename

        # Call Azure OpenAI TTS API
        response = client.audio.speech.create(
            model="TekstTilTale",  # Your deployment name
            voice=voice,
            input=text
        )

        # Save the audio file
        response.stream_to_file(str(filepath))

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
