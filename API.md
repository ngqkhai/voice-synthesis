# Voice Synthesis Service API Documentation

## Base URL
```
http://your-deployment-url/api/v1/voice
```

## Endpoints

### List Available Languages
```
GET /languages
```

Response:
```json
{
  "en-US": "English (US)",
  "es-ES": "Spanish (Spain)",
  "fr-FR": "French (France)"
}
```

### List Available Voices
```
GET /voices?language={language_code}[&category={category}]
```

Query Parameters:
- `language` (required): Language code (e.g., en-US, es-ES, fr-FR)
- `category` (optional): Filter voices by category
  - `kids`: Child-friendly voices
  - `scientific`: Professional voices for scientific content
  - `general`: Standard voices

Response:
```json
{
  "kids": [
  {
      "id": "en-US-Neural2-A",
    "name": "Friendly Female",
      "speed": 1.2
    },
    {
      "id": "en-US-Neural2-C",
      "name": "Playful Male",
      "speed": 1.2
    }
  ],
  "scientific": [
  {
    "id": "en-US-Neural2-D",
      "name": "Professional Female",
      "speed": 0.9
  }
]
}
```

### Synthesize Speech
```
POST /synthesize
```

Request Body:
```json
{
  "text": "Text to convert to speech",
  "voice_id": "en-US-Neural2-A",
  "language": "en-US",
  "speed": 1.0
}
```

Response:
```json
{
  "voice_id": "456f7890-1234-5678-90ab-cdef12345678",
  "audio_url": "/static/audio/456f7890-1234-5678-90ab-cdef12345678.mp3",
  "cloudinary_url": "https://res.cloudinary.com/your-cloud/video/upload/v1234567890/voice-synthesis/456f7890-1234-5678-90ab-cdef12345678.mp3",
  "duration": 10.0
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Language not supported"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": "Validation error message"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message"
}
```

## Example Usage

### Python
```python
import requests

# List available languages
languages = requests.get("http://your-deployment-url/api/v1/voice/languages").json()
print("Available languages:", languages)

# Choose a language
language = "en-US"  # or "es-ES", "fr-FR"

# List voices for the selected language
voices = requests.get(
    "http://your-deployment-url/api/v1/voice/voices",
    params={"language": language, "category": "kids"}
).json()

# Choose a voice
voice = voices["kids"][0]  # First kids voice

# Synthesize speech
response = requests.post(
    "http://your-deployment-url/api/v1/voice/synthesize",
    json={
        "text": "Hello, this is a test.",
        "voice_id": voice["id"],
        "language": language,
        "speed": voice["speed"]
    }
)
result = response.json()

# Access the audio URLs
local_audio_url = f"http://your-deployment-url{result['audio_url']}"
cloudinary_url = result['cloudinary_url']
print(f"Local audio URL: {local_audio_url}")
print(f"Cloudinary URL: {cloudinary_url}")
```

### JavaScript/TypeScript
```typescript
// List available languages
const languages = await fetch("http://your-deployment-url/api/v1/voice/languages")
  .then(res => res.json());
console.log("Available languages:", languages);

// Choose a language
const language = "en-US";  // or "es-ES", "fr-FR"

// List voices for the selected language
const voices = await fetch(
  `http://your-deployment-url/api/v1/voice/voices?language=${language}&category=kids`
).then(res => res.json());

// Choose a voice
const voice = voices.kids[0];  // First kids voice

// Synthesize speech
const response = await fetch("http://your-deployment-url/api/v1/voice/synthesize", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    text: "Hello, this is a test.",
    voice_id: voice.id,
    language: language,
    speed: voice.speed
  })
});
const result = await response.json();

// Access the audio URLs
const localAudioUrl = `http://your-deployment-url${result.audio_url}`;
const cloudinaryUrl = result.cloudinary_url;
console.log("Local audio URL:", localAudioUrl);
console.log("Cloudinary URL:", cloudinaryUrl);
``` 