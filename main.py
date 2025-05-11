from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import uuid
from datetime import datetime
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import asyncio
from app.providers.google_tts import GoogleTTSProvider
from app.message_broker import VoiceMessageBroker
import logging


# Load environment variables
load_dotenv()

# Configure root Python logger to output INFO-level logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

startup_logger = logging.getLogger("voice-synth.startup")

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

app = FastAPI()

# Initialize and start the RabbitMQ message broker for voice synthesis
broker = VoiceMessageBroker()

@app.on_event("startup")
async def start_broker():
    startup_logger.info("🚀 Startup event beginning")
    await broker.connect()
    startup_logger.info("✅ Broker connected, starting consumer")
    asyncio.create_task(broker.consume_messages())

@app.on_event("shutdown")
async def shutdown_broker():
    await broker.close()

# Mount static files directory
os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize TTS provider
tts_provider = GoogleTTSProvider()

class VoiceInfo(BaseModel):
    id: str
    name: str
    speed: float

class VoiceRequest(BaseModel):
    text: str
    voice_id: str = "en-US-Neural2-A"
    language: str = "en-US"
    speed: float = 1.0

class VoiceResponse(BaseModel):
    voice_id: str
    audio_url: str
    cloudinary_url: str
    duration: float

def upload_to_cloudinary(file_path: str, folder: str = "voice-synthesis") -> str:
    """Upload a file to Cloudinary and return the secure URL"""
    try:
        result = cloudinary.uploader.upload(
            file_path,
            resource_type="video",  # Use 'video' for audio files
            folder=folder,
            use_filename=True,
            unique_filename=True
        )
        return result["secure_url"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to Cloudinary: {str(e)}")

@app.get("/api/v1/voice/languages", response_model=Dict[str, str])
async def list_languages():
    """List available languages"""
    return tts_provider.get_languages()

@app.get("/api/v1/voice/voices", response_model=Dict[str, List[VoiceInfo]])
async def list_voices(
    language: str = Query(..., description="Language code (e.g., en-US, es-ES, fr-FR)"),
    category: Optional[str] = Query(None, description="Filter voices by category: kids, scientific, or general")
):
    """List available voices for a language, optionally filtered by category"""
    try:
        return tts_provider.get_voices(language, category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/voice/synthesize", response_model=VoiceResponse)
async def synthesize_voice(request: VoiceRequest):
    try:
        # Generate unique ID for this voice synthesis
        voice_id = str(uuid.uuid4())
        
        # Generate audio file
        audio_path = f"static/audio/{voice_id}.mp3"
        duration = await tts_provider.synthesize_speech(
            text=request.text,
            voice_id=request.voice_id,
            language_code=request.language,
            output_path=audio_path,
            speaking_rate=request.speed,
            pitch=0.0  # Default pitch
)

        # Upload to Cloudinary
        cloudinary_url = upload_to_cloudinary(audio_path)
        
        # Return response
        return VoiceResponse(
            voice_id=voice_id,
            audio_url=f"/static/audio/{voice_id}.mp3",
            cloudinary_url=cloudinary_url,
            duration=duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
