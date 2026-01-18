# Text-to-Speech Application

A web application for converting text to speech using Azure OpenAI TTS and Azure Speech Service with Danish and English language support. Branded for Gladsaxe Kommune.

## Features

- 🎙️ **Dual TTS Services** - Choose between Azure OpenAI TTS or Azure Speech Service
- 🇩🇰 **Danish & UK English Support** - Optimized for Danish with UK English alternatives
- 🌐 **Bilingual UI** - Switch between Danish and English interface
- 🗣️ **Multiple Voices** - Danish (Christel, Jeppe) and UK English (Sonia, Ryan)
- ⚡ **Speed Control** - Adjust speech rate from 0.75x to 1.5x
- 🎵 **High Quality Audio** - MP3/WAV output with automatic cleanup
- ▶️ **Browser Playback** - Listen directly in your browser
- 📥 **Download Support** - Save generated audio files in MP3 or WAV format
- 🧹 **Auto Cleanup** - Removes audio files older than 1 hour
- 🎨 **Clean & Responsive UI** with Gladsaxe Kommune branding
- 🔒 **Production-Ready** with security features
- 🐳 **Docker Support** with Nginx reverse proxy for SSL/TLS
- 🔐 **HTTPS Support** - Nginx proxy with your own certificates
- 👤 **User Authentication** - Secure login system with password protection
- 🔑 **User Management** - Self-service registration (can be disabled)
- 🛡️ **Access Control** - All TTS features require authentication
- ⏱️ **Rate Limiting** - Protects API usage with configurable request limits
- 🔵 **Azure AD Integration** - Single sign-on with Microsoft accounts (optional)
- 💾 **SQLite Storage** - Robust, thread-safe user database for local storage

## Prerequisites

- Python 3.13 or higher
- Azure OpenAI account with TTS API access **OR** Azure Speech Service
- API keys and endpoints from Azure

## Setup Instructions

### Development Setup (Local Testing)

For local development and testing outside of Docker:

#### 1. Clone or Download

Navigate to the project directory:
```bash
cd TTSApp-main
```

#### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Azure Services

Create a `.env` file in the project root:

```env
# Azure OpenAI Configuration (for OpenAI TTS service)
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-03-01-preview

# Azure Speech Service Configuration (for Speech service)
AZURE_SPEECH_KEY=your-speech-api-key
AZURE_SPEECH_REGION=swedencentral

# Authentication Configuration
SECRET_KEY=your-random-secret-key-here
REQUIRE_AUTHENTICATION=true
ALLOW_REGISTRATION=true

# Azure AD Configuration (optional - for Microsoft login)
AZURE_AD_CLIENT_ID=your-azure-ad-client-id
AZURE_AD_CLIENT_SECRET=your-azure-ad-client-secret
AZURE_AD_TENANT_ID=your-azure-ad-tenant-id
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

**Authentication Configuration:**
- `SECRET_KEY` - Random string for session encryption (generate with `python -c "import os; print(os.urandom(24).hex())"`)
- `REQUIRE_AUTHENTICATION` - Set to `true` to require login, `false` to disable authentication (default: `true`)
- `ALLOW_REGISTRATION` - Set to `true` to allow new user registration, `false` to disable (default: `true`)

**Azure AD Configuration (Optional):**
To enable "Sign in with Microsoft" button:
1. Register an app in [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Add redirect URI: `http://localhost/login/azure/callback` (and production URL)
3. Under Authentication, enable "ID tokens"
4. Under API permissions, add "Microsoft Graph - User.Read" and grant admin consent
5. Copy Client ID, Client Secret (create under Certificates & secrets), and Tenant ID to `.env`
6. Users will auto-register on first Azure AD login

#### 5. Create First User (Required)

Before running the application, you need to create at least one user account. You can do this by:

1. Setting `ALLOW_REGISTRATION=true` in your `.env` file
2. Starting the application
3. Navigating to the login page and clicking "Registrer her" / "Register here"
4. Creating your admin account
5. Optionally setting `ALLOW_REGISTRATION=false` to disable further registrations

**Note:** User data is stored in `users.json` with password hashing using werkzeug.

#### 6. Run the Application (Development Mode)

For local development and testing:

```bash
python app.py
```

The application will start on `http://localhost:5000`

**Note:** This runs Flask's development server, which is suitable for testing but not for production. For production deployment, use Docker (see below).

#### 7. Use the Application

1. Open your browser and go to `http://localhost:5000`
2. **Log in:** Enter your username and password
3. **Choose language:** Click 🇩🇰 for Danish or 🇬🇧 for English in the top-right corner
3. **Select service:** Choose between Azure OpenAI TTS or Azure Speech Service
   - Voices will automatically update based on your service selection
4. **Select voice:** Pick from available voices (Danish voices listed first for Speech Service)
5. **Adjust speed:** Use the slider to control speech rate (0.75x - 1.5x)
7. Enter the text you want to convert to speech
8. Click "Generer tale" (or "Generate Speech")
9. Listen to the audio in the browser player
10. **Download:** Choose MP3 or WAV format and click the download button
11. **Log out:** Click the logout button when finished

**Keyboard shortcut:** Press `Ctrl+Enter` in the text area to generate speech quickly

**Note:** The voice selector dynamically loads appropriate voices based on your selected TTS service to prevent errors.

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

## User Authentication

The application includes a flexible authentication system with support for both local accounts and Azure AD (Microsoft) login:

### Authentication Modes

**Optional Authentication:**
- Set `REQUIRE_AUTHENTICATION=false` to disable all authentication
- App becomes publicly accessible without login
- Useful for internal deployments or kiosk mode

**Local Authentication:**
- Username/password login with secure password hashing
- SQLite database storage in `data/users.db`
- Self-service registration (can be disabled)

**Azure AD Integration:**
- "Sign in with Microsoft" button on login page
- Single sign-on with organizational Microsoft accounts
- Auto-registers Azure AD users on first login
- Works alongside local authentication as fallback

### Features
- **Login System** - Flask-Login based session management
- **Password Security** - Werkzeug password hashing with salted pbkdf2:sha256
- **User Storage** - SQLite user database (`data/users.db`)
- **Rate Limiting** - Flask-Limiter for protecting endpoints
- **Self-Service Registration** - Users can create local accounts (optional)
- **Azure AD OAuth2** - Microsoft account integration via MSAL library
- **Auto-Registration** - Azure AD users automatically get accounts on first login
- **Dual Authentication** - Local and Azure AD work simultaneously
- **Access Control** - All TTS features require authentication when enabled
- **Bilingual Forms** - Login/register pages support Danish and English

### User Management

**Creating Local Users:**
1. Enable registration: Set `ALLOW_REGISTRATION=true` in `.env`
2. Access the login page
3. Click "Registrer her" / "Register here"
4. Enter username and password (minimum 6 characters)
5. Log in with your new credentials

**Azure AD Users:**
1. Configure Azure AD credentials in `.env` (see setup section above)
2. Users click "Sign in with Microsoft" on login page
3. Authenticate with their Microsoft account
4. Automatically registered on first login
5. No password needed - uses Microsoft authentication

**Disabling Registration:**
- Set `ALLOW_REGISTRATION=false` in `.env`
- Restart the application: `docker-compose down && docker-compose up -d`
- The registration link will disappear from the login page
- Direct access to `/register` will redirect to login
- Azure AD login continues to work and auto-register users

**Disabling Authentication Completely:**
- Set `REQUIRE_AUTHENTICATION=false` in `.env`
- Restart the application
- App becomes publicly accessible without any login
- Useful for kiosk deployments or trusted internal networks

**User Data:**
- Stored in `data/users.db` (persistent across Docker restarts)
- Local users have password hashes (never plain text)
- Azure AD users have email and display name, no password
- User sessions use Flask's secure session management with `SECRET_KEY`

**Rate Limiting:**
- The `/generate-speech` endpoint is limited to **5 requests per minute** by default.
- General API usage is limited to **50 per hour** and **200 per day**.

**Security Notes:**
- Always set a strong `SECRET_KEY` in production
- Disable registration after creating admin accounts (if using local auth)
- Keep Azure AD client secret secure (never commit to git)
- Backup `data/users.json` to preserve user accounts
- The file is automatically created on first registration
- Azure AD users are marked with `is_azure_ad: true` flag

## Project Structure

```
TTSApp-main/
├── app.py              # Main Flask application with authentication and dual TTS
├── auth.py             # User authentication module (local + Azure AD)
├── wsgi.py             # Production WSGI entry point
├── requirements.txt    # Python dependencies (includes msal for Azure AD)
├── .env                # Your credentials (not in git)
├── .env.example        # Example environment configuration
├── .gitignore          # Git ignore file
├── Dockerfile          # Docker container definition
├── docker-compose.yml  # Docker Compose with Nginx proxy and auth volumes
├── .dockerignore       # Docker build exclusions
├── README.md           # This file
├── DOCKER.md           # Docker deployment guide
├── certs/              # SSL/TLS certificates directory
│   ├── README.md       # Certificate setup instructions
│   ├── server.crt      # Your SSL certificate (not in git)
│   └── server.key      # Your private key (not in git)
├── nginx/              # Nginx reverse proxy configuration
│   └── nginx.conf      # Nginx server configuration
├── data/               # Persistent data directory (Docker volume)
│   ├── users.db        # SQLite user database (created automatically, not in git)
│   └── audio/          # Generated audio files (auto-cleaned after 1 hour)
├── templates/
│   ├── index.html      # Main TTS page with bilingual UI
│   ├── login.html      # Login page with Azure AD button
│   └── register.html   # Registration page (optional)
└── static/
    ├── style.css       # Responsive styles with Gladsaxe Kommune blue theme
    ├── script.js       # TTS frontend logic with dynamic voice loading
    ├── auth.js         # Authentication page language switcher
    ├── login.css       # Authentication page styles (includes Microsoft button)
    ├── gladsaxe-logo.png  # Gladsaxe Kommune logo
    └── audio/          # Legacy audio directory (not used in Docker)
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
- Verify script.js is loading correctly

### Voice selection issues
- Voices are loaded dynamically based on the selected service
- When switching services, the voice list updates automatically
- If voices don't load, check browser console for API errors
- Ensure the service you selected has valid credentials configured

### Speed control not working
- Ensure you're using a modern browser (Chrome, Firefox, Edge, Safari)
- For Azure OpenAI TTS: speed range is 0.75x-1.5x
- For Azure Speech Service: speed affects SSML prosody rate

## Production Deployment with Docker

For production deployment, the application uses Docker with an Nginx reverse proxy for SSL/TLS termination.

### Architecture

```
Internet/Network
    ↓
Nginx (Port 443/80) ← Your SSL/TLS Certificates
    ↓
Flask App (Internal Port 5000)
```

### Prerequisites

- Docker and Docker Compose installed
- SSL/TLS certificate files (e.g., from your organization's CA or Let's Encrypt)

### Quick Start with Docker

#### 1. Prepare SSL Certificates

Place your certificate files in the `certs/` directory:

```bash
cd certs/
# Copy your certificate files here
# Rename them to:
# - server.crt (your certificate or certificate chain)
# - server.key (your private key)

chmod 600 server.key
```

**Certificate Formats:**
- Both files should be in PEM format (Base64 encoded)
- If you have a certificate chain, concatenate them in `server.crt`:
  ```bash
  cat your-cert.crt intermediate.crt root.crt > server.crt
  ```

For detailed certificate instructions, see `certs/README.md`.

#### 2. Configure Environment

Create a `.env` file in the project root with your Azure credentials (see "Configure Azure Services" section above).

#### 3. Deploy

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Check status
docker ps

# Stop services
docker compose down
```

#### 4. Access the Application

- **HTTPS:** `https://your-domain.com` or `https://your-server-ip`
- **HTTP:** Automatically redirects to HTTPS

### Docker Services

The deployment includes two containers:

1. **nginx** - Reverse proxy with SSL/TLS
   - Ports: 80 (HTTP) → 443 (HTTPS)
   - Handles SSL termination
   - Forwards requests to Flask app
   - Automatic HTTP → HTTPS redirect

2. **tts-app** - Flask application
   - Internal port 5000 (not exposed externally)
   - Runs with Gunicorn WSGI server
   - Non-root user for security

### Security Features

The Docker deployment includes:
- ✅ **SSL/TLS encryption** via Nginx reverse proxy
- ✅ **HTTPS enforcement** with automatic HTTP redirect
- ✅ **Modern TLS configuration** (TLS 1.2/1.3 only)
- ✅ **Security headers** (HSTS, XSS protection, clickjacking prevention)
- ✅ **Non-root user execution** in containers
- ✅ **Production WSGI server** (Gunicorn)
- ✅ **Request size limits** (16MB)
- ✅ **Optimized timeouts** for long TTS operations (120s)

### Updating SSL Certificates

To update certificates:

```bash
# Replace certificate files in certs/ directory
cp new-cert.crt certs/server.crt
cp new-key.key certs/server.key
chmod 600 certs/server.key

# Restart Nginx to load new certificates
docker compose restart nginx
```

### Testing the Setup

```bash
# Test HTTPS connection
curl -I https://your-server-ip

# Test HTTP redirect
curl -I http://your-server-ip

# Check Nginx logs
docker logs tts-nginx

# Check Flask app logs
docker logs tts-poc
```

For more detailed Docker deployment information, see [DOCKER.md](DOCKER.md).

## Tech Stack

- **Backend:** Flask (Python 3.13)
- **TTS Services:** Azure OpenAI TTS + Azure Speech Service (REST API)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Styling:** Custom CSS with Gladsaxe Kommune blue branding (#0051A5)
- **Production Server:** Gunicorn with security headers
- **Reverse Proxy:** Nginx (Alpine) for SSL/TLS termination
- **Containerization:** Docker & Docker Compose
- **Audio Formats:** MP3 and WAV (user selectable for download)

## Language & Voice Support

The application supports:
- 🇩🇰 **Danish** (Christel, Jeppe) via Azure Speech Service
- 🇬🇧 **UK English** (Sonia, Ryan) via Azure Speech Service
- 🌍 **Multiple Languages** via Azure OpenAI TTS (Alloy, Echo, Fable, Onyx, Nova, Shimmer)

The UI can be switched between:
- 🇩🇰 **Danish** (default)
- 🇬🇧 **English**

## Audio Quality

- **Azure Speech Service:** 24kHz, MP3 or WAV output (user selectable)
- **Azure OpenAI TTS:** Adaptive quality based on model, MP3 format
- **Speed Range:** 0.75x to 1.5x (prevents audio distortion)
- **Auto Cleanup:** Files older than 1 hour are automatically deleted
- **Download Formats:** Users can choose between MP3 or WAV for downloading

## Security Features

The application includes:
- ✅ Environment variable configuration (secrets not in code)
- ✅ Production WSGI server (Gunicorn)
- ✅ Security headers (XSS, clickjacking, HSTS)
- ✅ Request size limits
- ✅ Non-root Docker user
- ✅ Secrets excluded from git (.gitignore)

## Contributing

This application is branded for Gladsaxe Kommune. Feel free to fork and customize for your organization with:
- Additional voice options
- More TTS services
- Advanced audio effects
- Text preprocessing features
- Custom branding and color schemes

## Branding

The current version includes:
- **Gladsaxe Kommune logo** displayed in the header
- **Blue color scheme** (#0051A5) matching Gladsaxe Kommune branding
- **Customizable UI** - Easy to rebrand by updating logo and CSS colors

To customize for your organization:
1. Replace `static/gladsaxe-logo.png` with your logo
2. Update the color scheme in `static/style.css` (search for `#0051A5`)
3. Update the page title in `templates/index.html`

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
