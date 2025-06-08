"""
Speech-to-Text (STT) Module for ELLMa

Provides speech recognition functionality using various backends.
"""

import os
import wave
import tempfile
import importlib
import warnings
from typing import Optional, Union, BinaryIO, Tuple, Dict, Any, Type, Any
from dataclasses import dataclass
from enum import Enum
from rich.console import Console

# Try to import audioop with fallback
try:
    import audioop
    AUDIOOP_AVAILABLE = True
except ImportError:
    AUDIOOP_AVAILABLE = False
    warnings.warn(
        "audioop module not found. Audio processing features will be limited. "
        "Install the 'audio' extra with: pip install ellma[audio]"
    )
    
    # Create a dummy audioop module
    class DummyAudioop:
        @staticmethod
        def add(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def adpcm2lin(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def alaw2lin(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def avg(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def avgpp(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def bias(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def cross(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def findfactor(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def findfit(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def findmax(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def getsample(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def lin2adpcm(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def lin2alaw(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def lin2lin(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def lin2ulaw(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def max(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def maxpp(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def minmax(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def mul(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def ratecv(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def reverse(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def rms(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def tomono(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def tostereo(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def ulaw2lin(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
        
        @staticmethod
        def get_sample_size(*args, **kwargs):
            raise ImportError("audioop module not available. Install the 'audio' extra with: pip install ellma[audio]")
    
    # Replace the audioop module with our dummy implementation
    import sys
    sys.modules['audioop'] = DummyAudioop()
    audioop = DummyAudioop()

# Define dummy classes first for fallback
class DummyAudioData:
    def __init__(self, *args, **kwargs):
        pass
    def get_wav_data(self, *args, **kwargs):
        return b''

class DummyRecognizer:
    def __init__(self, *args, **kwargs):
        pass
    def recognize_google(self, *args, **kwargs):
        raise ImportError("speech_recognition module not installed")
    def recognize_sphinx(self, *args, **kwargs):
        raise ImportError("speech_recognition module not installed")

# Initialize speech recognition variables
SPEECH_RECOGNITION_AVAILABLE = False
sr = None

# Try to import speech_recognition
try:
    import speech_recognition as sr
    # Check if the module has the required attributes
    if hasattr(sr, 'AudioData') and hasattr(sr, 'Recognizer'):
        SPEECH_RECOGNITION_AVAILABLE = True
    else:
        # If the module is imported but missing required attributes
        class DummySR:
            AudioData = DummyAudioData
            Recognizer = DummyRecognizer
        sr = DummySR()
        SPEECH_RECOGNITION_AVAILABLE = False
except ImportError:
    # Create a dummy module-like object with the required attributes
    class DummySR:
        AudioData = DummyAudioData
        Recognizer = DummyRecognizer
    
    sr = DummySR()
    SPEECH_RECOGNITION_AVAILABLE = False

# Try to import whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Custom exception for missing dependencies
class DependencyError(ImportError):
    """Exception raised when a required dependency is missing."""
    def __init__(self, package_name: str, feature: str):
        self.package_name = package_name
        self.feature = feature
        super().__init__(
            f"The '{package_name}' package is required for {feature} but is not installed. "
            f"Please install it with: pip install {package_name}"
        )

class STTBackend(Enum):
    """Available STT backends"""
    WHISPER = "whisper"  # OpenAI's Whisper (offline)
    GOOGLE = "google"    # Google Web Speech API (online)
    SPHINX = "sphinx"    # CMU Sphinx (offline)

@dataclass
class STTConfig:
    """Configuration for STT"""
    backend: STTBackend = STTBackend.WHISPER
    language: str = "en-US"
    energy_threshold: int = 300  # Minimum audio energy for speech detection
    pause_threshold: float = 0.8  # Seconds of non-speaking audio before a phrase is considered complete
    dynamic_energy_threshold: bool = True  # Adjust energy threshold based on ambient noise
    timeout: Optional[float] = None  # Seconds to wait for audio input before giving up
    phrase_time_limit: Optional[float] = None  # Maximum seconds a phrase can be recorded

class STTModule:
    """Speech-to-Text module for ELLMa"""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize STT module with configuration"""
        self.config = STTConfig(**(config or {}))
        self.console = Console()
        self.recognizer = None
        self.available_backends = self._check_available_backends()
        self._init_recognizer()
    
    def _check_available_backends(self) -> Dict[str, bool]:
        """Check which STT backends are available"""
        return {
            'whisper': WHISPER_AVAILABLE,
            'google': SPEECH_RECOGNITION_AVAILABLE,
            'sphinx': SPEECH_RECOGNITION_AVAILABLE
        }
    
    def _require_backend(self, backend_name: str):
        """Check if a backend is available, raise helpful error if not"""
        if not self.available_backends.get(backend_name, False):
            if backend_name == 'whisper' and not WHISPER_AVAILABLE:
                raise DependencyError('whisper', 'offline speech recognition')
            elif backend_name in ['google', 'sphinx'] and not SPEECH_RECOGNITION_AVAILABLE:
                raise DependencyError('SpeechRecognition', f'{backend_name} speech recognition')
            else:
                raise ValueError(f"Unsupported backend: {backend_name}")
    
    def _init_recognizer(self):
        """Initialize the speech recognizer with configuration"""
        if not SPEECH_RECOGNITION_AVAILABLE and not WHISPER_AVAILABLE:
            self.console.print(
                "[yellow]Warning: No STT backends available. "
                "Install SpeechRecognition and/or whisper for speech recognition.[/yellow]"
            )
            return
            
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = self.config.energy_threshold
            self.recognizer.pause_threshold = self.config.pause_threshold
            self.recognizer.dynamic_energy_threshold = self.config.dynamic_energy_threshold
        
        # Initialize whisper if available and needed
        if self.config.backend == STTBackend.WHISPER and WHISPER_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model("base")
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to load Whisper model: {e}[/yellow]")
                self.available_backends['whisper'] = False
                if self.config.backend == STTBackend.WHISPER:
                    self.config.backend = STTBackend.GOOGLE if SPEECH_RECOGNITION_AVAILABLE else None
    
    def _get_available_backend(self) -> Optional[STTBackend]:
        """Get the first available backend"""
        if self.available_backends.get('whisper', False):
            return STTBackend.WHISPER
        elif self.available_backends.get('google', False):
            return STTBackend.GOOGLE
        elif self.available_backends.get('sphinx', False):
            return STTBackend.SPHINX
        return None
    
    def listen(self, timeout: Optional[float] = None, phrase_time_limit: Optional[float] = None) -> Optional[str]:
        """
        Listen to microphone and return recognized text
        
        Args:
            timeout: Seconds to wait for audio input before giving up
            phrase_time_limit: Maximum seconds a phrase can be recorded
            
        Returns:
            str: Recognized text, or None if no speech detected or error occurred
        """
        timeout = timeout or self.config.timeout
        phrase_time_limit = phrase_time_limit or self.config.phrase_time_limit
        
        with sr.Microphone() as source:
            self.console.print("[yellow]Listening... (speak now)[/yellow]")
            
            try:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                
                # Listen to the microphone
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                return self.recognize(audio)
                
            except sr.WaitTimeoutError:
                self.console.print("[yellow]No speech detected[/yellow]")
                return None
            except Exception as e:
                self.console.print(f"[red]Error in speech recognition: {e}[/red]")
                return None
    
    def recognize(self, audio_data: sr.AudioData) -> Optional[str]:
        """
        Recognize speech from audio data
        
        Args:
            audio_data: AudioData object from speech_recognition
            
        Returns:
            str: Recognized text, or None if recognition failed
        """
        try:
            if self.config.backend == STTBackend.WHISPER:
                return self._recognize_whisper(audio_data)
            elif self.config.backend == STTBackend.GOOGLE:
                return self._recognize_google(audio_data)
            else:  # SPHINX
                return self._recognize_sphinx(audio_data)
        except Exception as e:
            self.console.print(f"[red]Recognition error: {e}[/red]")
            return None
    
    def _recognize_whisper(self, audio_data: sr.AudioData) -> Optional[str]:
        """Use Whisper for speech recognition"""
        if not WHISPER_AVAILABLE:
            self.console.print("[red]Whisper is not available. Please install it with: pip install whisper[/red]")
            return None
            
        try:
            # Convert AudioData to WAV data
            wav_data = audio_data.get_wav_data()
            
            # Save to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(wav_data)
                temp_filename = f.name
            
            try:
                # Transcribe using whisper
                result = self.whisper_model.transcribe(temp_filename, language=self.config.language)
                return result["text"]
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_filename)
                except:
                    pass
                    
        except Exception as e:
            self.console.print(f"[red]Whisper error: {e}[/red]")
            return None
    
    def _recognize_google(self, audio_data: sr.AudioData) -> Optional[str]:
        """Use Google Web Speech API for speech recognition"""
        try:
            return self.recognizer.recognize_google(
                audio_data,
                language=self.config.language
            )
        except sr.UnknownValueError:
            self.console.print("[yellow]Google Speech Recognition could not understand audio[/yellow]")
            return None
        except sr.RequestError as e:
            self.console.print(f"[red]Could not request results from Google Speech Recognition service; {e}[/red]")
            return None
    
    def _recognize_sphinx(self, audio_data: sr.AudioData) -> Optional[str]:
        """Use CMU Sphinx for offline speech recognition"""
        try:
            return self.recognizer.recognize_sphinx(
                audio_data,
                language=self.config.language
            )
        except sr.UnknownValueError:
            self.console.print("[yellow]Sphinx could not understand audio[/yellow]")
            return None
        except sr.RequestError as e:
            self.console.print(f"[red]Sphinx error; {e}[/red]")
            return None
    
    def recognize_from_file(self, filename: str, backend: str = None) -> Optional[str]:
        """
        Recognize speech from an audio file
        
        Args:
            filename: Path to audio file (WAV format)
            backend: STT backend to use (whisper, google, sphinx)
            
        Returns:
            str: Recognized text, or None if recognition failed
        """
        # If no backends are available, return None
        if not any(self.available_backends.values()):
            self.console.print("[red]No STT backends available. Please install SpeechRecognition and/or whisper.[/red]")
            return None
            
        try:
            # Update backend if specified
            if backend:
                backend = backend.lower()
                self._require_backend(backend)
                self.config.backend = STTBackend(backend)
            
            # If no backend is set, use the first available one
            if not hasattr(self, 'config') or not self.config.backend:
                available = self._get_available_backend()
                if not available:
                    self.console.print("[red]No STT backends available[/red]")
                    return None
                self.config.backend = available
            
            # Use the appropriate method based on backend
            if self.config.backend == STTBackend.WHISPER and WHISPER_AVAILABLE:
                try:
                    result = self.whisper_model.transcribe(filename, language=self.config.language)
                    return result["text"]
                except Exception as e:
                    self.console.print(f"[red]Whisper error: {e}[/red]")
                    return None
            elif SPEECH_RECOGNITION_AVAILABLE and self.recognizer:
                try:
                    with sr.AudioFile(filename) as source:
                        audio = self.recognizer.record(source)
                        return self.recognize(audio)
                except Exception as e:
                    self.console.print(f"[red]Error processing audio file: {e}[/red]")
                    return None
            else:
                self.console.print(f"[red]Backend {self.config.backend} is not available[/red]")
                return None
                
        except Exception as e:
            self.console.print(f"[red]Error in recognize_from_file: {e}[/red]")
            return None

# Command-line interface for testing
if __name__ == "__main__":
    stt = STTModule()
    print("Testing STT module. Press Ctrl+C to exit.")
    
    try:
        while True:
            text = stt.listen()
            if text:
                print(f"You said: {text}")
    except KeyboardInterrupt:
        print("\nExiting...")
