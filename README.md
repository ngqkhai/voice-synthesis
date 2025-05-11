# Voice Synthesis Service

A FastAPI-based service that provides text-to-speech capabilities using Google Cloud Text-to-Speech API.

## Features

- Text-to-speech conversion with multiple voice options
- Support for different audience types:
  - General audience
  - Kids (child-friendly voices)
  - Scientific content (professional voices)
- Multiple output formats (MP3)
- Customizable voice parameters (pitch, speaking rate)
- RESTful API with clear documentation

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Cloud credentials:
   - Place your Google Cloud service account key file in `secrets/google-credentials.json`
   - Set the environment variable:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS=secrets/google-credentials.json
     ```

3. Run the service:
```bash
uvicorn app.main:app --reload
```

## API Documentation

See [API.md](API.md) for detailed API documentation.

## Project Structure

```
voice-synthesis/
├── app/                    # Application code
│   ├── providers/         # TTS providers
│   ├── models.py          # Data models
│   └── __init__.py        # Package initialization
├── tests/                 # Test files
├── static/               # Static files (audio)
├── requirements.txt     # Python dependencies
├── .gitignore         # Git exclusions
├── API.md             # API documentation
└── README.md          # This file
```

## Development

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install development dependencies:
```bash
pip install -r requirements.txt
```

3. Run tests:
```bash
pytest
```

## Security Notes

- Never commit credentials to version control
- Use environment variables for sensitive information
- Rotate credentials regularly
- Use different credentials for development and production
