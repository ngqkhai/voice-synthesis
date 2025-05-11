from google.cloud import texttospeech
import os
import asyncio
from typing import Optional, Dict, List
import logging
import json

logger = logging.getLogger(__name__)

class GoogleTTSProvider:
    def __init__(self):
        # Create credentials from environment variables
        credentials = {
            "type": os.getenv("GOOGLE_TYPE"),
            "project_id": os.getenv("GOOGLE_PROJECT_ID"),
            "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GOOGLE_PRIVATE_KEY"),
            "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
            "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN")
        }
        
        # Check if all required credentials are present
        missing_credentials = [key for key, value in credentials.items() if not value]
        if missing_credentials:
            raise ValueError(
                f"Missing required Google Cloud credentials: {', '.join(missing_credentials)}. "
                "Please set them in your .env file."
            )
        
        # Create a temporary credentials file
        temp_credentials_path = "/tmp/google-credentials.json"
        with open(temp_credentials_path, "w") as f:
            json.dump(credentials, f)
        
        # Set the environment variable
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_credentials_path
        
        # Initialize the client
        self.client = texttospeech.TextToSpeechClient()
        
        # Fetch all available voices from Google Cloud TTS
        self.voices = {}
        self.languages = {}
        
        try:
            # Get all available voices
            voices = self.client.list_voices()
            
            # Organize voices by language and category
            for voice in voices.voices:
                language_code = voice.language_codes[0]
                voice_id = voice.name
                
                # Add language if not exists
                if language_code not in self.languages:
                    self.languages[language_code] = {
                        "name": self._get_language_name(language_code),
                        "voices": {
                            "kids": [],
                            "scientific": [],
                            "general": []
                        }
                    }
                
                # Categorize voice based on name and language
                category = self._categorize_voice(voice_id, language_code)
                
                # Add voice to appropriate category
                voice_info = {
                    "id": voice_id,
                    "name": self._get_voice_name(voice_id, language_code),
                    "speed": self._get_voice_speed(category)
                }
                
                self.languages[language_code]["voices"][category].append(voice_info)
                
        except Exception as e:
            logger.error(f"Error fetching voices: {str(e)}")
            raise

    def _get_language_name(self, language_code: str) -> str:
        """Get display name for a language code"""
        # Add more language mappings as needed
        language_names = {
            "en-US": "English (US)",
            "en-GB": "English (UK)",
            "es-ES": "Spanish (Spain)",
            "es-MX": "Spanish (Mexico)",
            "fr-FR": "French (France)",
            "de-DE": "German",
            "it-IT": "Italian",
            "ja-JP": "Japanese",
            "ko-KR": "Korean",
            "pt-BR": "Portuguese (Brazil)",
            "ru-RU": "Russian",
            "zh-CN": "Chinese (Mandarin)",
            "zh-TW": "Chinese (Taiwan)",
            "hi-IN": "Hindi",
            "ar-XA": "Arabic",
            "nl-NL": "Dutch",
            "pl-PL": "Polish",
            "sv-SE": "Swedish",
            "tr-TR": "Turkish",
            "da-DK": "Danish",
            "fi-FI": "Finnish",
            "nb-NO": "Norwegian",
            "cs-CZ": "Czech",
            "el-GR": "Greek",
            "hu-HU": "Hungarian",
            "ro-RO": "Romanian",
            "sk-SK": "Slovak",
            "uk-UA": "Ukrainian",
            "vi-VN": "Vietnamese",
            "th-TH": "Thai",
            "id-ID": "Indonesian",
            "ms-MY": "Malay",
            "fil-PH": "Filipino"
        }
        return language_names.get(language_code, language_code)

    def _categorize_voice(self, voice_id: str, language_code: str) -> str:
        """Categorize voice based on its ID and language"""
        # Check for kid-friendly voices
        if any(keyword in voice_id.lower() for keyword in ["child", "kids", "friendly", "playful"]):
            return "kids"
        
        # Check for scientific/professional voices
        if any(keyword in voice_id.lower() for keyword in ["professional", "serious", "scientific", "news"]):
            return "scientific"
        
        # Default to general
        return "general"

    def _get_voice_name(self, voice_id: str, language_code: str) -> str:
        """Get display name for a voice ID"""
        # Remove language code and standardize name
        name = voice_id.replace(f"{language_code}-", "")
        name = name.replace("Wavenet-", "")
        
        # Map voice IDs to friendly names
        voice_names = {
            "A": "Friendly Female",
            "B": "Playful Male",
            "C": "Warm Female",
            "D": "Professional Female",
            "E": "Serious Male",
            "F": "Standard Male",
            "G": "Confident Female",
            "H": "Calm Male",
            "I": "Enthusiastic Female",
            "J": "Authoritative Male"
        }
        
        # Get the last character as the voice identifier
        voice_key = name[-1]
        return voice_names.get(voice_key, name)

    def _get_voice_speed(self, category: str) -> float:
        """Get default speaking rate for a voice category"""
        speeds = {
            "kids": 1.2,
            "scientific": 0.9,
            "general": 1.0
        }
        return speeds.get(category, 1.0)

    def get_languages(self) -> Dict[str, str]:
        """Get available languages and their display names"""
        return {code: info["name"] for code, info in self.languages.items()}

    def get_voices(self, language_code: str, category: Optional[str] = None) -> Dict[str, List[Dict]]:
        """Get available voices for a language, optionally filtered by category"""
        if language_code not in self.languages:
            raise ValueError(f"Language {language_code} not supported")
        
        voices = self.languages[language_code]["voices"]
        if category:
            return {category: voices.get(category, [])}
        return voices

    async def synthesize_speech(
        self,
        text: str,
        voice_id: str = "en-US-Neural2-A",
        language_code: str = "en-US",
        output_path: str = "output.mp3",
        speaking_rate: float = 1.0,
        pitch: float = 0.0
    ) -> float:
        """Synthesize speech from text using Google Cloud TTS"""
        try:
            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_id,
            )
            
            # Select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch
            )

            # Perform the text-to-speech request
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            # Save the audio content to a file
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as out:
                    out.write(response.audio_content)

            # Calculate duration (approximate)
            # MP3 files are typically 16kHz, 1 channel, 16-bit
            # This is a rough estimate
            duration = len(response.audio_content) / (16000 * 2)  # seconds
            
            return duration

        except Exception as e:
            logger.error(f"Error in synthesize_speech: {str(e)}")
            raise 