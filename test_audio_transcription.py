#!/usr/bin/env python3
"""Test audio transcription with WhisperX."""

import asyncio
import base64
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import InputProcessor using importlib to handle hyphenated directory name
import importlib.util
spec = importlib.util.spec_from_file_location(
    "input_processor",
    os.path.join(os.path.dirname(__file__), "services/input-processor/main.py")
)
input_processor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(input_processor_module)
InputProcessor = input_processor_module.InputProcessor
from shared.utils.logging import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)


async def test_with_sample_audio():
    """Test with a sample audio file."""
    print("=" * 60)
    print("WhisperX Audio Transcription Test")
    print("=" * 60)
    print()

    # Check if we have a sample audio file
    sample_audio_path = "test_audio.wav"

    if not os.path.exists(sample_audio_path):
        print(f"❌ Sample audio file '{sample_audio_path}' not found.")
        print()
        print("To test, you need to:")
        print("1. Record a short audio message (e.g., 'There is a pothole on 5th avenue')")
        print("2. Save it as 'test_audio.wav' in the project root")
        print("3. Run this script again")
        print()
        print("Alternative: Testing with text-to-speech generated audio...")
        print()

        # Try to generate sample audio with pyttsx3 or gtts if available
        try:
            await test_generate_sample_audio()
        except Exception as e:
            print(f"Could not generate sample audio: {e}")
            print()
            print("You can also test by sending audio to the API:")
            print("  curl -X POST http://localhost:8000/api/v2/triage \\")
            print("    -H 'Content-Type: application/json' \\")
            print("    -d '{\"audio\": \"<base64-encoded-audio>\"}'")

        return

    print(f"✅ Found sample audio file: {sample_audio_path}")
    print()

    # Read the audio file
    with open(sample_audio_path, 'rb') as f:
        audio_bytes = f.read()

    file_size_kb = len(audio_bytes) / 1024
    print(f"📊 Audio file size: {file_size_kb:.2f} KB")
    print()

    # Encode to base64 (as would come from API)
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    print(f"📦 Base64 encoded length: {len(audio_base64)} characters")
    print()

    # Initialize processor
    processor = InputProcessor()

    print("🎤 Starting transcription with WhisperX...")
    print("   (This may take a moment on first run to download the model)")
    print()

    # Process the audio
    result = await processor.process(audio_base64)

    print("=" * 60)
    print("TRANSCRIPTION RESULTS")
    print("=" * 60)
    print()
    print(f"📝 Transcribed Text: {result.text}")
    print(f"🎯 Confidence: {result.confidence:.2%}")
    print(f"🌐 Language: {result.language}")
    print()

    if result.confidence > 0.7:
        print("✅ Transcription successful!")
    elif result.confidence > 0.3:
        print("⚠️  Transcription completed with low confidence")
    else:
        print("❌ Transcription failed or returned no text")

    print()
    return result


async def test_generate_sample_audio():
    """Generate a sample audio file for testing."""
    try:
        from gtts import gTTS
        import tempfile

        print("🔊 Generating sample audio with Google Text-to-Speech...")

        text = "There is a large pothole on Fifth Avenue near Pine Street that needs repair"
        tts = gTTS(text=text, lang='en')

        # Save to temporary file then move to test location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            tts.save(tmp.name)

            # Convert MP3 to WAV using pydub if available
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_mp3(tmp.name)
                audio.export("test_audio.wav", format="wav")
                os.unlink(tmp.name)
                print("✅ Generated test_audio.wav")
                print()
                await test_with_sample_audio()
            except ImportError:
                # Just use MP3 file
                os.rename(tmp.name, "test_audio.mp3")
                print("✅ Generated test_audio.mp3")
                print("   (Install pydub and ffmpeg to convert to WAV)")
                print()

    except ImportError:
        print("❌ gTTS not installed. Install with: pip install gtts")
        print()


async def test_with_text():
    """Test that text input still works."""
    print("=" * 60)
    print("Testing Text Input (Sanity Check)")
    print("=" * 60)
    print()

    processor = InputProcessor()
    text_input = "There's a broken streetlight on 5th Avenue"

    print(f"📝 Input: {text_input}")
    print()

    result = await processor.process(text_input)

    print(f"✅ Processed Text: {result.text}")
    print(f"🎯 Confidence: {result.confidence:.2%}")
    print(f"🌐 Language: {result.language}")
    print()


async def main():
    """Run all tests."""
    # Test text input first
    await test_with_text()

    # Test audio input
    await test_with_sample_audio()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
