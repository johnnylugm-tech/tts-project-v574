"""
Pytest configuration for TTS project
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock external dependencies BEFORE any imports
sys.modules['ffmpeg'] = MagicMock()
sys.modules['ffmpeg-python'] = MagicMock()
sys.modules['edge_tts'] = MagicMock()
sys.modules['edge_tts'].SubMaker = MagicMock()
sys.modules['edge_tts']. Communicate = MagicMock()

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))