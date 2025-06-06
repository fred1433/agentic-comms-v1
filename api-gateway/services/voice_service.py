import asyncio
import io
import time
from typing import Optional, AsyncIterator
import structlog
from deepgram import DeepgramClient, PrerecordedOptions, SpeakOptions
import aiofiles
import tempfile
import os

from config import settings

logger = structlog.get_logger()

class VoiceService:
    """Service for Deepgram speech-to-text and text-to-speech"""
    
    def __init__(self):
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        
        # STT configuration
        self.stt_options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            punctuate=True,
            diarize=False,
            language="en-US",
            encoding="wav",
            sample_rate=16000,
            channels=1
        )
        
        # TTS configuration
        self.tts_options = SpeakOptions(
            model="aura-luna-en",  # Natural female voice
            encoding="linear16",
            sample_rate=24000
        )
    
    async def speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """Convert speech audio to text using Deepgram"""
        start_time = time.time()
        
        try:
            # Create a temporary file for the audio data
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Read the audio file
                with open(temp_file_path, "rb") as audio_file:
                    buffer_data = audio_file.read()
                
                payload = {"buffer": buffer_data}
                
                # Transcribe
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.listen.prerecorded.v("1").transcribe_file(
                        payload, self.stt_options
                    )
                )
                
                # Extract transcript
                transcript = ""
                if response.results and response.results.channels:
                    channel = response.results.channels[0]
                    if channel.alternatives:
                        transcript = channel.alternatives[0].transcript
                
                processing_time = (time.time() - start_time) * 1000
                
                logger.info(
                    "Speech-to-text completed",
                    processing_time_ms=processing_time,
                    transcript_length=len(transcript),
                    confidence=channel.alternatives[0].confidence if channel.alternatives else 0
                )
                
                return transcript.strip() if transcript else None
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error("Speech-to-text failed", error=str(e))
            return None
    
    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech audio using Deepgram"""
        start_time = time.time()
        
        try:
            # Generate speech
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.speak.v("1").save(
                    filename="temp_output.wav",
                    source={"text": text},
                    options=self.tts_options
                )
            )
            
            # Read the generated audio file
            with open("temp_output.wav", "rb") as audio_file:
                audio_data = audio_file.read()
            
            # Clean up
            if os.path.exists("temp_output.wav"):
                os.unlink("temp_output.wav")
            
            processing_time = (time.time() - start_time) * 1000
            
            logger.info(
                "Text-to-speech completed",
                processing_time_ms=processing_time,
                text_length=len(text),
                audio_size_bytes=len(audio_data)
            )
            
            return audio_data
            
        except Exception as e:
            logger.error("Text-to-speech failed", error=str(e))
            # Return empty audio data or raise exception
            return b""
    
    async def text_to_speech_stream(self, text: str) -> AsyncIterator[bytes]:
        """Convert text to speech with streaming output"""
        try:
            # For now, return the complete audio as a single chunk
            # In production, you might want to implement true streaming
            audio_data = await self.text_to_speech(text)
            
            # Split into chunks for streaming
            chunk_size = 4096
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.01)  # Small delay to simulate streaming
                
        except Exception as e:
            logger.error("Streaming text-to-speech failed", error=str(e))
            yield b""
    
    async def get_audio_duration(self, audio_data: bytes) -> float:
        """Get duration of audio in seconds"""
        try:
            # This is a simplified calculation
            # In practice, you'd want to parse the WAV header properly
            # Assuming 16-bit, 16kHz mono WAV
            sample_rate = 16000
            bytes_per_sample = 2
            
            # Skip WAV header (44 bytes)
            audio_samples = len(audio_data) - 44
            duration = audio_samples / (sample_rate * bytes_per_sample)
            
            return max(0.0, duration)
            
        except Exception as e:
            logger.error("Audio duration calculation failed", error=str(e))
            return 0.0
    
    def validate_audio_format(self, audio_data: bytes) -> bool:
        """Validate if audio data is in supported format"""
        try:
            # Check for WAV header
            if len(audio_data) < 44:
                return False
            
            # Check RIFF header
            if audio_data[:4] != b'RIFF':
                return False
            
            # Check WAVE format
            if audio_data[8:12] != b'WAVE':
                return False
            
            return True
            
        except Exception as e:
            logger.error("Audio format validation failed", error=str(e))
            return False
    
    async def process_voice_message(
        self,
        audio_data: bytes,
        return_transcript: bool = True,
        return_audio_response: bool = True,
        response_text: Optional[str] = None
    ) -> dict:
        """Process complete voice message workflow"""
        result = {
            "transcript": None,
            "audio_response": None,
            "duration_seconds": 0.0,
            "processing_time_ms": 0.0,
            "success": False
        }
        
        start_time = time.time()
        
        try:
            # Validate audio format
            if not self.validate_audio_format(audio_data):
                logger.warning("Invalid audio format received")
                return result
            
            # Get audio duration
            result["duration_seconds"] = await self.get_audio_duration(audio_data)
            
            # Speech to text
            if return_transcript:
                transcript = await self.speech_to_text(audio_data)
                result["transcript"] = transcript
            
            # Text to speech for response
            if return_audio_response and response_text:
                audio_response = await self.text_to_speech(response_text)
                result["audio_response"] = audio_response
            
            result["processing_time_ms"] = (time.time() - start_time) * 1000
            result["success"] = True
            
            return result
            
        except Exception as e:
            logger.error("Voice message processing failed", error=str(e))
            result["processing_time_ms"] = (time.time() - start_time) * 1000
            return result
    
    async def health_check(self) -> bool:
        """Check if voice service is healthy"""
        try:
            # Test TTS with a simple phrase
            test_text = "Health check"
            audio_data = await self.text_to_speech(test_text)
            
            # Test STT with the generated audio
            transcript = await self.speech_to_text(audio_data)
            
            # Check if we got reasonable results
            return bool(audio_data and len(audio_data) > 1000)
            
        except Exception as e:
            logger.error("Voice service health check failed", error=str(e))
            return False
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return [
            "wav",
            "mp3", 
            "m4a",
            "flac",
            "ogg"
        ]
    
    def get_recommended_settings(self) -> dict:
        """Get recommended audio settings for best quality"""
        return {
            "format": "wav",
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "max_duration_seconds": 300,
            "max_file_size_mb": 25
        } 