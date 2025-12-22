# Text-to-Speech POC

A simple web application for converting text to speech using Azure OpenAI's TTS API with Danish language support.

## Features

- 🎙️ Text-to-speech conversion with Azure OpenAI
- 🇩🇰 **Danish language support** (also supports 50+ other languages)
- 🌐 **Bilingual UI** - Switch between Danish and English
- 🗣️ Multiple voice options (Alloy, Echo, Fable, Onyx, Nova, Shimmer)
- ▶️ Audio playback directly in the browser
- 📥 Download generated audio files
- 🎨 Clean and responsive UI
- 🔒 Production-ready with security features
- 🐳 Docker support for easy deployment

## Prerequisites

- Python 3.8 or higher
- Azure OpenAI account with TTS API access
- API key and endpoint from Azure OpenAI

## Setup Instructions

### 1. Clone or Download

Navigate to the project directory:
```bash
cd "TTS POC"
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Azure OpenAI

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your Azure OpenAI credentials:
```
AZURE_OPENAI_API_KEY=your-actual-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
```

**To get these credentials:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Go to "Keys and Endpoint"
4. Copy Key 1 (or Key 2) and the Endpoint

**Deploy the TTS Model:**
1. In your Azure OpenAI resource, go to "Model deployments" or "Azure OpenAI Studio"
2. Deploy the `tts-1` model (or `tts-1-hd` for higher quality)
3. Set the deployment name to `TekstTilTale` (or update `model=` in [app.py](app.py#L67) to match your deployment name)

### 5. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### 6. Use the Application

1. Open your browser and go to `http://localhost:5000`
2. **Choose language:** Click 🇩🇰 for Danish or 🇬🇧 for English in the top-right corner
3. Enter the text you want to convert to speech (in Danish or any language)
4. Select a voice from the dropdown
5. Click "Generer tale" (or "Generate Speech")
6. Listen to the audio or download it

**Keyboard shortcut:** Press `Ctrl+Enter` in the text area to generate speech quickly

## Available Voices

- **Alloy** - Neutral and balanced
- **Echo** - Male voice
- **Fable** - British accent
- **Onyx** - Deep male voice
- **Nova** - Female voice
- **Shimmer** - Soft female voice

## Project Structure
 with security headers
├── wsgi.py             # Production WSGI entry point
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .env                # Your credentials (not in git)
├── .gitignore          # Git ignore file
├── Dockerfile          # Docker container definition
├── docker-compose.yml  # Docker Compose configuration
├── .dockerignore       # Docker build exclusions
├── README.md           # This file
├── DOCKER.md           # Docker deployment guide
├── templates/
│   └── index.html      # Main HTML page with i18n
└── static/
    ├── style.css       # Responsive styles
    ├── script.js       # Frontend logic with translations
    └── audio/          # Generated audio files (auto-created
    ├── style.css      # Styles
    ├── script.js      # Frontend JavaScript
    └── audio/         # Generated audio files (created automatically)
```

## Troubleshooting
the `tts-1` model deployed
- Ensure the deployment name matches the one in [app.py](app.py#L67)
- Ensure there are no extra spaces in your credentials

### Audio not generating
- Check your Azure OpenAI quota and usage limits
- Verify that the TTS model is deployed in your Azure resource
- Check the browser console for any JavaScript errors
- Ensure your deployment name is `TekstTilTale` or update app.py

### Language switching not working
- Clear your browser cache and refresh the page
- Check browser console for JavaScript errors

## Docker Deployment

For production deployment with Docker, see [DOCKER.md](DOCKER.md) for complete instructions.

### Quick Start with Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Security Features

The Docker deployment includes:
- ✅ Non-root user execution
- ✅ Production WSGI server (Gunicorn)
- ✅ Security headers (XSS, clickjacking protection)
- ✅ Request size limits
- ✅ HSTS headers for HTTPS

## Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **TTS Engine:** Azure OpenAI TTS API
- **Production Server:** Gunicorn
- **Containerization:** Docker & Docker Compose
- **Deployment:** Ready for production with security hardening
- ✅ Minimal container image

## Language Support

The application automatically detects and speaks Danish (and 50+ other languages). The UI can be switched between:
- 🇩🇰 **Danish** (default)
- 🇬🇧 **English**

All voices support multilingual text - just type in your desired language!
EXPOSE 5000

CMD ["python", "app.py"]
```

Then run with:
```bash
docker build -t tts-poc .
docker run -p 5000:5000 --env-file .env tts-poc
```

## License

This is a POC (Proof of Concept) project for demonstration purposes.
