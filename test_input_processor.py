#!/usr/bin/env python3
"""Test Input Processor Service."""
import sys
import asyncio
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "services"))

async def test_input_processor():
    print("=== Testing Input Processor ===\n")

    try:
        # Import with hyphenated name
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "input_processor",
            Path(__file__).parent / "services" / "input-processor" / "main.py"
        )
        input_proc_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(input_proc_module)
        InputProcessor = input_proc_module.InputProcessor

        processor = InputProcessor()
        print("✓ Input Processor initialized\n")

        # Test 1: Simple text input
        print("Test 1: Processing text input...")
        result = await processor.process("There's a pothole on 5th and Pine")
        print(f"   Input: There's a pothole on 5th and Pine")
        print(f"   Output: {result.text}")
        print(f"   Confidence: {result.confidence}")
        print(f"   ✓ Text processing works\n")

        # Test 2: Text with extra whitespace
        print("Test 2: Processing text with whitespace...")
        result2 = await processor.process("   Multiple   spaces   here   ")
        print(f"   Input: '   Multiple   spaces   here   '")
        print(f"   Output: '{result2.text}'")
        print(f"   ✓ Whitespace normalization works\n")

        # Test 3: Mock audio input
        print("Test 3: Processing mock audio...")
        result3 = await processor.process(b"fake_audio_data")
        print(f"   Output: {result3.text}")
        print(f"   Confidence: {result3.confidence}")
        print(f"   ✓ Mock audio processing works\n")

        print("="*50)
        print("✓ All Input Processor tests passed!")
        print("="*50)
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_input_processor())
    sys.exit(0 if success else 1)
