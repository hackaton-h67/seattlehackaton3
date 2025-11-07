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
        """Process text input with normalization."""
        import re

        # Remove extra whitespace
        normalized = ' '.join(text.split())

        # Fix common contractions
        contractions = {
            "there's": "there is",
            "it's": "it is",
            "that's": "that is",
            "what's": "what is",
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "doesn't": "does not",
            "isn't": "is not",
            "wasn't": "was not",
            "weren't": "were not",
            "hasn't": "has not",
            "haven't": "have not",
            "hadn't": "had not"
        }

        for contraction, expansion in contractions.items():
            normalized = re.sub(r'\b' + contraction + r'\b', expansion, normalized, flags=re.IGNORECASE)

        # Basic cleaning
        normalized = normalized.strip()

        # Calculate confidence (simple heuristic based on length and punctuation)
        confidence = 1.0
        if len(normalized) < 10:
            confidence = 0.7
        elif len(normalized) < 5:
            confidence = 0.5

        logger.info("text_processed", original_length=len(text), normalized_length=len(normalized))

        return ProcessedInput(
            text=normalized,
            confidence=confidence,
            language="en"
        )

    async def _process_audio(self, audio_data: Union[str, bytes]) -> ProcessedInput:
        """Process audio input using faster-whisper."""
        if settings.mock_audio_processing:
            return ProcessedInput(
                text="[MOCK] Audio transcription not implemented",
                confidence=0.9,
                language="en"
            )

        try:
            from faster_whisper import WhisperModel
            import tempfile
            import os

            logger.info("starting_audio_transcription")

            # 1. Decode base64 if needed
            if isinstance(audio_data, str):
                audio_bytes = base64.b64decode(audio_data)
            else:
                audio_bytes = audio_data

            # 2. Save to temporary file (Whisper needs a file path)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_bytes)
                audio_path = tmp_file.name

            try:
                # 3. Transcribe using faster-whisper
                # Use 'base' model for speed, 'large-v2' or 'large-v3' for accuracy
                model_size = "base"
                device = "cpu"  # Use CPU for better compatibility
                compute_type = "int8"  # int8 for CPU

                logger.info("loading_whisper_model", model=model_size, device=device, compute_type=compute_type)

                # Load faster-whisper model
                model = WhisperModel(model_size, device=device, compute_type=compute_type)

                # Transcribe audio
                logger.info("transcribing_audio", path=audio_path)
                segments, info = model.transcribe(audio_path, beam_size=5, language="en")

                # Collect segments and calculate confidence
                transcribed_segments = []
                total_confidence = 0.0
                segment_count = 0

                for segment in segments:
                    transcribed_segments.append(segment.text)
                    # faster-whisper provides avg_logprob which can be used as confidence
                    # Convert logprob to confidence (logprob is negative, closer to 0 is better)
                    segment_confidence = min(1.0, max(0.0, (segment.avg_logprob + 1.0)))
                    total_confidence += segment_confidence
                    segment_count += 1

                # Join all segments
                transcribed_text = " ".join(transcribed_segments).strip()

                # Calculate average confidence
                if segment_count > 0:
                    confidence = total_confidence / segment_count
                else:
                    confidence = 0.5 if transcribed_text else 0.0

                # Get detected language
                language = info.language if hasattr(info, 'language') else "en"

                logger.info(
                    "audio_transcribed",
                    text_length=len(transcribed_text),
                    confidence=confidence,
                    language=language,
                    segments=segment_count
                )

                # 4. Return normalized text with confidence
                return ProcessedInput(
                    text=transcribed_text,
                    confidence=confidence,
                    language=language
                )

            finally:
                # Clean up temporary file
                if os.path.exists(audio_path):
                    os.unlink(audio_path)

        except ImportError as e:
            logger.error("faster_whisper_not_available", error=str(e))
            return ProcessedInput(
                text="Audio processing requires faster-whisper installation",
                confidence=0.0,
                language="en"
            )
        except Exception as e:
            logger.error("audio_transcription_failed", error=str(e))
            return ProcessedInput(
                text="Audio transcription failed",
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
