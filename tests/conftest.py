"""
Test configuration and fixtures for ELLMa tests.
"""

import pytest
import sys
import importlib
import importlib.util
from unittest.mock import MagicMock, patch

# Mock audioop module if not available
if not importlib.util.find_spec('audioop'):
    import tests.mock_audioop as audioop
    sys.modules['audioop'] = audioop
    AUDIOOP_AVAILABLE = True
else:
    AUDIOOP_AVAILABLE = True

# Skip tests that require audio dependencies if they're not available
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_audio: mark test as requiring audio dependencies"
    )
    config.addinivalue_line(
        "markers",
        "requires_audioop: mark test as requiring the audioop module"
    )

@pytest.fixture(autouse=True)
def mock_audio_dependencies(monkeypatch):
    """Mock audio dependencies if they're not available."""
    if not SPEECH_RECOGNITION_AVAILABLE:
        # Mock the speech_recognition module
        mock_sr = MagicMock()
        mock_audio = MagicMock()
        mock_recognizer = MagicMock()
        mock_audio.AudioData = MagicMock()
        mock_sr.AudioData = MagicMock()
        mock_sr.Recognizer = MagicMock(return_value=mock_recognizer)
        
        monkeypatch.setitem(sys.modules, 'speech_recognition', mock_sr)
        monkeypatch.setitem(sys.modules, 'ellma.modules.stt.sr', mock_sr)
        
        # Also mock the STT module
        mock_stt = MagicMock()
        mock_stt.STTModule = MagicMock()
        monkeypatch.setitem(sys.modules, 'ellma.modules.stt', mock_stt)

# Custom markers for tests that require specific dependencies
skip_if_no_audio = pytest.mark.skipif(
    not SPEECH_RECOGNITION_AVAILABLE,
    reason="Test requires audio dependencies (speech_recognition)"
)

skip_if_no_audioop = pytest.mark.skipif(
    not AUDIOOP_AVAILABLE,
    reason="Test requires audioop module"
)
