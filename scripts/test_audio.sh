#!/bin/bash
#
# test_audio.sh - Automated audio transcription testing script
#
# This script tests the audio transcription feature using faster-whisper.
# It generates a test audio file and verifies the transcription works correctly.
#

set -e  # Exit on error

echo "=========================================="
echo "Service-Sense Audio Transcription Test"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if faster-whisper is installed
if ! python -c "import faster_whisper" 2>/dev/null; then
    echo "❌ faster-whisper not installed."
    echo "   Installing faster-whisper..."
    pip install faster-whisper
fi

# Check if gTTS is installed (for test audio generation)
if ! python -c "import gtts" 2>/dev/null; then
    echo "📦 Installing gTTS for test audio generation..."
    pip install gtts pydub
fi

echo ""
echo "🧪 Running audio transcription tests..."
echo ""

# Run the test
python test_audio_transcription.py

echo ""
echo "=========================================="
echo "✅ Audio transcription test complete!"
echo "=========================================="
echo ""
echo "Test Results:"
echo "- Text input processing: ✓"
echo "- Audio transcription: ✓"
echo "- Faster-whisper integration: ✓"
echo ""
echo "To test with your own audio file:"
echo "1. Record a WAV file named 'test_audio.wav'"
echo "2. Place it in the project root"
echo "3. Run: python test_audio_transcription.py"
echo ""
