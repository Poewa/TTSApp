# Text-to-Speech Application

A web application for converting text to speech using Azure OpenAI TTS and Azure Speech Service with Danish and English language support.

## Features

- 🎙️ **Dual TTS Services** - Choose between Azure OpenAI TTS or Azure Speech Service
- 🇩🇰 **Danish & UK English Support** - Optimized for Danish with UK English alternatives
- 🌐 **Bilingual UI** - Switch between Danish and English interface
- 🗣️ **Multiple Voices** - Danish (Christel, Jeppe) and UK English (Sonia, Ryan)
- ⚡ **Speed Control** - Adjust speech rate from 0.75x to 1.5x
- 🎵 **High Quality Audio** - 96kbps/24kHz MP3 output
- ▶️ **Browser Playback** - Listen directly in your browser
- 📥 **Download Support** - Save generated audio files
- 🧹 **Auto Cleanup** - Removes audio files older than 1 hour
- 🎨 **Clean & Responsive UI**
- 🔒 **Production-Ready** with security features
- 🐳 **Docker Support** for easy deployment

## Prerequisites

- Python 3.13 or higher
- Azure OpenAI account with TTS API access **OR** Azure Speech Service
- API keys and endpoints from Azure

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

### 4. Configure Azure Services

Create a `.env` file in the project root:

```env
# Azure OpenAI Configuration (for OpenAI TTS service)
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-03-01-preview

# Azure Speech Service Configuration (for Speech service)
AZURE_SPEECH_KEY=your-speech-api-key
AZURE_SPEECH_REGION=swedencentral
```

**To get Azure OpenAI credentials:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Go to "Keys and Endpoint"
4. Copy Key 1 and the Endpoint
5. Deploy the `tts-1-hd` model with deployment name `tts-hd`

**To get Azure Speech Service credentials:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Create or navigate to your Speech Service resource
3. Go to "Keys and Endpoint"
4. Copy Key 1 and the Region

### 5. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### 6. Use the Application

1. Open your browser and go to `http://localhost:5000`
2. **Choose language:** Click 🇩🇰 for Danish or 🇬🇧 for English in the top-right corner
3. **Select service:** Choose between Azure OpenAI TTS or Azure Speech Service
4. **Select voice:** Pick from available voices (Danish voices listed first)
5. **Adjust speed:** Use the slider to control speech rate (0.75x - 1.5x)
6. Enter the text you want to convert to speech
7. Click "Generer tale" (or "Generate Speech")
8. Listen to the audio or download it

**Keyboard shortcut:** Press `Ctrl+Enter` in the text area to generate speech quickly

## Available Voices

### Azure Speech Service (Default)
- **Christel (DK Female)** - Natural Danish female voice
- **Jeppe (DK Male)** - Natural Danish male voice
- **Sonia (UK Female)** - British English female voice
- **Ryan (UK Male)** - British English male voice

### Azure OpenAI TTS
- **Alloy** - Neutral and balanced
- **Echo** - Male voice
- **Fable** - British accent
- **Onyx** - Deep male voice
- **Nova** - Female voice
- **Shimmer** - Soft female voice

## Project Structure

```
TTS POC/
├── app.py              # Main Flask application with dual TTS service support
├── wsgi.py             # Production WSGI entry point
├── requirements.txt    # Python dependencies
├── .env                # Your credentials (not in git)
├── .gitignore          # Git ignore file
├── Dockerfile          # Docker container definition
├── docker-compose.yml  # Docker Compose configuration
├── .dockerignore       # Docker build exclusions
├── README.md           # This file
├── DOCKER.md           # Docker deployment guide
├── data/
│   └── audio/          # Persistent audio storage (Docker volume)
├── templates/
│   └── index.html      # Main HTML page with bilingual UI
└── static/
    ├── style.css       # Responsive styles
    ├── script.js       # Frontend logic with service switching
    └── audio/          # Generated audio files (auto-cleaned after 1 hour)
```

## Troubleshooting

### Azure OpenAI TTS Issues
- Verify you have the `tts-1-hd` model deployed as `tts-hd`
- Ensure the deployment name matches the one in [app.py](app.py)
- Check your Azure OpenAI quota and usage limits
- Ensure there are no extra spaces in your credentials

### Azure Speech Service Issues
- Verify your Speech Service key and region are correct
- Check that the region matches your resource (e.g., `swedencentral`)
- Ensure the REST API endpoint is accessible from your network
- Check browser console for HTTP errors (401 = auth issue, 403 = quota/region issue)

### Audio not generating
- Switch between services to isolate the issue (OpenAI TTS vs Speech Service)
- Check the browser console for JavaScript errors
- Verify environment variables are loaded: `docker-compose exec web env | grep AZURE`
- Check container logs: `docker-compose logs -f web`

### Language switching not working
- Clear your browser cache and hard refresh (Ctrl+Shift+R)
- Check browser console for JavaScript errors
- Verify script.js is loading with cache-busting parameter (?v=3)

### Speed control not working
- Ensure you're using a modern browser (Chrome, Firefox, Edge, Safari)
- For Azure OpenAI TTS: speed range is 0.75x-1.5x
- For Azure Speech Service: speed affects SSML prosody rate

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

- **Backend:** Flask (Python 3.13)
- **TTS Services:** Azure OpenAI TTS + Azure Speech Service (REST API)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Production Server:** Gunicorn with security headers
- **Containerization:** Docker & Docker Compose
- **Audio Format:** MP3 (96kbps/24kHz for Speech Service)

## Language & Voice Support

The application supports:
- 🇩🇰 **Danish** (Christel, Jeppe) via Azure Speech Service
- 🇬🇧 **UK English** (Sonia, Ryan) via Azure Speech Service
- 🌍 **Multiple Languages** via Azure OpenAI TTS (Alloy, Echo, Fable, Onyx, Nova, Shimmer)

The UI can be switched between:
- 🇩🇰 **Danish** (default)
- 🇬🇧 **English**

## Audio Quality

- **Azure Speech Service:** 24kHz, 96kbps MP3
- **Azure OpenAI TTS:** Adaptive quality based on model
- **Speed Range:** 0.75x to 1.5x (prevents audio distortion)
- **Auto Cleanup:** Files older than 1 hour are automatically deleted

## Security Features

The application includes:
- ✅ Environment variable configuration (secrets not in code)
- ✅ Production WSGI server (Gunicorn)
- ✅ Security headers (XSS, clickjacking, HSTS)
- ✅ Request size limits
- ✅ Non-root Docker user
- ✅ Secrets excluded from git (.gitignore)

## Contributing

This is a proof of concept application. Feel free to extend it with:
- Additional voice options
- More TTS services
- Advanced audio effects
- Text preprocessing features

## License

This project is for demonstration purposes.

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
