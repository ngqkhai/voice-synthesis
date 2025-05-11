from .google_tts import GoogleTTSProvider

def get_provider() -> GoogleTTSProvider:
    """Get a TTS provider instance"""
    return GoogleTTSProvider()

__all__ = ['GoogleTTSProvider', 'get_provider']
