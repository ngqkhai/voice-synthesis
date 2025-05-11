import requests
import json
import os
import logging
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_to_cloudinary(file_path: str, folder: str = "voice-synthesis") -> dict:
    """Upload a file to Cloudinary"""
    try:
        logger.info(f"Uploading {file_path} to Cloudinary...")
        result = cloudinary.uploader.upload(
            file_path,
            resource_type="video",  # Use 'video' for audio files
            folder=folder,
            use_filename=True,
            unique_filename=False
        )
        logger.info(f"Upload successful! URL: {result['secure_url']}")
        return result
    except Exception as e:
        logger.error(f"Failed to upload to Cloudinary: {str(e)}")
        raise

def test_single_voice():
    """Test voice synthesis with a single language and voice"""

    # Base URL for the API
    base_url = "http://localhost:8000/api/v1/voice"

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Get available languages
        logger.info("Getting available languages...")
        response = requests.get(f"{base_url}/languages")
        if response.status_code != 200:
            logger.error(f"Failed to get languages: {response.status_code} {response.reason}")
            logger.error(f"Response content: {response.text}")
            return
        
        languages = response.json()
        logger.info("\nAvailable languages:")
        for code, name in languages.items():
            logger.info(f"- {code}: {name}")

        # Choose a language (you can change this to test different languages)
        language_code = "en-US"  # Change this to test different languages
        logger.info(f"\nSelected language: {language_code}")

        # Get voices for the selected language
        response = requests.get(f"{base_url}/voices", params={"language": language_code})
        if response.status_code != 200:
            logger.error(f"Failed to get voices: {response.status_code} {response.reason}")
            logger.error(f"Response content: {response.text}")
            return
        
        voices = response.json()
        logger.info("\nAvailable voice categories:")
        for category, voice_list in voices.items():
            logger.info(f"\n{category.upper()} voices:")
            for voice in voice_list:
                logger.info(f"- {voice['name']} (ID: {voice['id']})")

        # Choose a voice category (you can change this to test different categories)
        category = "general"  # Change this to test different categories
        if category not in voices or not voices[category]:
            logger.error(f"No {category} voices available for {language_code}")
            return

        # Get the first voice in the selected category
        voice = voices[category][0]
        logger.info(f"\nSelected voice: {voice['name']}")

        # Sample text for testing
        text = "Hello! This is a test of the voice synthesis service. We are testing a single voice to ensure everything works correctly."

        # Prepare request
        request_data = {
            "text": text,
            "voice_id": voice["id"],
            "language": language_code,
            "speed": voice["speed"]
        }

        logger.info("Sending synthesis request...")
        logger.info(f"Request data: {json.dumps(request_data, indent=2)}")

        # Send request
        response = requests.post(
            f"{base_url}/synthesize",
            json=request_data
        )

        if response.status_code != 200:
            logger.error(f"Synthesis failed: {response.status_code} {response.reason}")
            logger.error(f"Response content: {response.text}")
            return

        # Get response data
        result = response.json()
        audio_url = f"http://localhost:8000{result['audio_url']}"

        # Download audio
        logger.info(f"Downloading audio from: {result['audio_url']}")
        audio_response = requests.get(audio_url)
        
        if audio_response.status_code != 200:
            logger.error(f"Failed to download audio: {audio_response.status_code} {audio_response.reason}")
            return

        # Save audio file
        output_file = f"test_{language_code}_{category}_voice.mp3"
        output_path = os.path.join(output_dir, output_file)
        with open(output_path, "wb") as f:
            f.write(audio_response.content)

        # Log results
        file_size = os.path.getsize(output_path)
        logger.info(f"Audio saved to: {output_path}")
        logger.info(f"File size: {file_size} bytes")
        logger.info(f"Duration: {result['duration']} seconds")

        # Upload to Cloudinary
        cloudinary_result = upload_to_cloudinary(output_path)
        logger.info(f"Cloudinary upload details: {json.dumps(cloudinary_result, indent=2)}")

        logger.info("\nTest completed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_single_voice() 