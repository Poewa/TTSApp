import pytest
from unittest.mock import patch
from pathlib import Path
from app import app, limiter


@pytest.fixture
def noauth_client():
    """Client with authentication disabled and rate limiting off, for exercising
    the generation endpoints directly."""
    app.config['TESTING'] = True
    app.config['REQUIRE_AUTHENTICATION'] = False
    app.config['SECRET_KEY'] = 'test_secret_key'
    limiter.enabled = False
    with app.test_client() as client:
        with app.app_context():
            yield client
    limiter.enabled = True


def test_home_page_redirects(client):
    """Test that home page redirects to login if auth is required"""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Log ind' in response.data or b'Login' in response.data

def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Brugernavn' in response.data


# --- Combined (Danish + English) generation ---

def test_combined_requires_both_texts(noauth_client):
    """Missing one language should be rejected with 400."""
    response = noauth_client.post('/generate-combined', json={
        'text_da': 'Kun dansk',
        'voice_da': 'da-DK-ChristelNeural',
        'voice_en': 'en-GB-SoniaNeural',
        'service': 'speech'
    })
    assert response.status_code == 400


def test_combined_text_too_long(noauth_client):
    """Text exceeding MAX_TEXT_LENGTH per language should be rejected."""
    long_text = 'a' * (app.config['MAX_TEXT_LENGTH'] + 1)
    response = noauth_client.post('/generate-combined', json={
        'text_da': long_text,
        'text_en': 'Hello',
        'voice_da': 'da-DK-ChristelNeural',
        'voice_en': 'en-GB-SoniaNeural',
        'service': 'speech'
    })
    assert response.status_code == 400


def test_combined_requires_voice_per_language(noauth_client):
    """A missing voice for either language should be rejected."""
    response = noauth_client.post('/generate-combined', json={
        'text_da': 'Hej',
        'text_en': 'Hello',
        'voice_da': 'da-DK-ChristelNeural',
        'service': 'speech'
    })
    assert response.status_code == 400


def test_combined_happy_path_danish_first(noauth_client):
    """Happy path: synthesizes Danish then English and concatenates into one file."""
    fake_da = Path('data/audio/aaaaaaaa-0000-0000-0000-000000000000.mp3')
    fake_en = Path('data/audio/bbbbbbbb-0000-0000-0000-000000000000.mp3')
    with patch('app.synthesize_to_file', side_effect=[fake_da, fake_en]) as mock_synth, \
         patch('app.concatenate_audio') as mock_concat:
        response = noauth_client.post('/generate-combined', json={
            'text_da': 'Hej verden',
            'text_en': 'Hello world',
            'voice_da': 'da-DK-ChristelNeural',
            'voice_en': 'en-GB-SoniaNeural',
            'service': 'speech',
            'speed': 1.0
        })

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['filename'].endswith('.mp3')
    assert data['audio_url'].startswith('/audio/')
    assert mock_synth.call_count == 2
    assert mock_concat.call_count == 1
    # Danish must be synthesized first (text is the first positional arg)
    assert mock_synth.call_args_list[0][0][0] == 'Hej verden'
    assert mock_synth.call_args_list[1][0][0] == 'Hello world'
    # Concatenation order is [danish, english]
    segments = mock_concat.call_args_list[0][0][0]
    assert segments == [fake_da, fake_en]


def test_generate_speech_still_works(noauth_client):
    """Regression: the refactored single-text endpoint still returns the file."""
    fake = Path('data/audio/cccccccc-0000-0000-0000-000000000000.mp3')
    with patch('app.synthesize_to_file', return_value=fake):
        response = noauth_client.post('/generate-speech', json={
            'text': 'Hello',
            'voice': 'alloy',
            'service': 'openai',
            'speed': 1.0
        })
    assert response.status_code == 200
    assert response.get_json()['filename'] == fake.name
