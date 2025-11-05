"""
Input Processor Service - Handles text and audio input processing.
"""

from typing import Union
import base64
from shared.models.request import ProcessedInput
from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging(settings.log_level)
logger = get_logger(__name__)


class InputProcessor:
    """Process text and audio inputs."""

    def __init__(self):
        self.whisper_model = None
        if settings.enable_audio_input and not settings.mock_audio_processing:
            # TODO: Initialize WhisperX model
            # self.whisper_model = WhisperX(model=settings.whisper_model, language="en")
            logger.info("audio_processing_enabled", model=settings.whisper_model)

    async def process(self, input_data: Union[str, bytes]) -> ProcessedInput:
        """
        Process text or audio input.

        Args:
            input_data: Text string or base64 encoded audio

        Returns:
            ProcessedInput with normalized text
        """
        if isinstance(input_data, bytes) or self._is_audio(input_data):
            return await self._process_audio(input_data)
        return await self._process_text(input_data)

    async def _process_text(self, text: str) -> ProcessedInput:
        """Process text input."""
        # TODO: Implement text normalization
        # - Remove extra whitespace
        # - Fix common typos
        # - Expand contractions
        normalized = text.strip()

        return ProcessedInput(
            text=normalized,
            confidence=1.0,
            language="en"
        )

    async def _process_audio(self, audio_data: Union[str, bytes]) -> ProcessedInput:
        """Process audio input using WhisperX."""
        if settings.mock_audio_processing:
            return ProcessedInput(
                text="[MOCK] Audio transcription not implemented",
                confidence=0.9,
                language="en"
            )

        # TODO: Implement audio transcription
        # 1. Decode base64 if needed
        # 2. Validate audio format and duration
        # 3. Transcribe using WhisperX
        # 4. Return normalized text with confidence

        logger.warning("audio_processing_not_implemented")
        return ProcessedInput(
            text="Audio processing coming soon",
            confidence=0.0,
            language="en"
        )

    def _is_audio(self, data: str) -> bool:
        """Check if input is audio data."""
        if isinstance(data, str):
            try:
                # Check if it's valid base64
                base64.b64decode(data)
                return len(data) > 1000  # Arbitrary threshold
            except Exception:
                return False
        return True


if __name__ == "__main__":
    import asyncio

    async def test():
        processor = InputProcessor()
        result = await processor.process("There's a pothole on 5th and Pine")
        print(result)

    asyncio.run(test())
