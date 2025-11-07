# Audio Transcription Feature

Service-Sense supports audio input for citizen service requests using **faster-whisper**, an optimized implementation of OpenAI's Whisper model.

## Overview

The audio transcription feature allows citizens to:
- Submit service requests by voice instead of typing
- Report issues while on the go
- Provide detailed descriptions naturally

## Technical Implementation

### Architecture

The audio transcription pipeline consists of:

1. **Audio Input**: Base64-encoded audio data (WAV, MP3, or other formats)
2. **Preprocessing**: Decode and save to temporary file
3. **Transcription**: faster-whisper model processes audio
4. **Post-processing**: Extract text, confidence, and language
5. **Output**: Normalized text with confidence score

### Implementation Details

**Location**: `services/input-processor/main.py`

**Key Components**:
- **Model**: faster-whisper base model (can upgrade to large-v2/large-v3)
- **Device**: CPU by default (GPU supported with CUDA)
- **Compute Type**: int8 for CPU, float16 for GPU
- **Language**: English only (configurable)
- **Confidence**: Calculated from segment-level log probabilities

### Why faster-whisper?

We chose **faster-whisper** over whisperx because:
1. **Stability**: Better compatibility with PyTorch 2.9.0+
2. **Performance**: CTranslate2 backend provides 4x faster inference
3. **Memory**: Lower memory footprint than standard Whisper
4. **Accuracy**: Same accuracy as OpenAI Whisper
5. **Simplicity**: Easier to deploy and maintain

## Configuration

### Environment Variables

```bash
# .env configuration
ENABLE_AUDIO_INPUT=true
MOCK_AUDIO_PROCESSING=false  # Set to false for real transcription

# Audio settings
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large, large-v2, large-v3
WHISPER_LANGUAGE=en
WHISPER_DEVICE=cpu  # cpu or cuda
WHISPER_COMPUTE_TYPE=int8  # int8 for CPU, float16 for GPU
AUDIO_MAX_DURATION=300  # seconds (5 minutes)
AUDIO_SAMPLE_RATE=16000
```

### Model Selection

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny | 39M | Fastest | Basic | Quick testing |
| base | 74M | Fast | Good | **Default - balanced** |
| small | 244M | Medium | Better | Production |
| medium | 769M | Slow | Very Good | High accuracy needs |
| large-v2 | 1550M | Slowest | Best | Maximum accuracy |
| large-v3 | 1550M | Slowest | Best | Latest improvements |

## Testing

### Automated Testing

```bash
# Run automated test script
./scripts/test_audio.sh
```

This script:
1. Checks dependencies (faster-whisper, gTTS)
2. Generates test audio using Google Text-to-Speech
3. Tests text input processing (sanity check)
4. Tests audio transcription
5. Reports results with confidence scores

### Manual Testing

```bash
# Run test directly
python test_audio_transcription.py

# With custom audio file
# 1. Place your audio file as 'test_audio.wav'
# 2. Run the test
python test_audio_transcription.py
```

### API Testing

```bash
# Encode audio to base64
base64 -w 0 my_audio.wav > audio_base64.txt

# Send to API
curl -X POST http://localhost:8000/api/v2/triage \
  -H "Content-Type: application/json" \
  -d "{
    \"audio\": \"$(cat audio_base64.txt)\",
    \"location\": {
      \"latitude\": 47.6115,
      \"longitude\": -122.3344
    }
  }"
```

## Performance

### Benchmarks (Base Model on CPU)

- **5-second audio**: ~1-2 seconds processing
- **30-second audio**: ~4-6 seconds processing
- **Memory usage**: ~500MB-1GB
- **First run**: Additional time for model download (~75MB)

### GPU Acceleration

For faster processing, enable GPU:

```bash
# Install CUDA-enabled PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Update .env
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
```

**GPU Performance** (NVIDIA GPU with CUDA):
- 5-10x faster than CPU
- Better for large models (large-v2, large-v3)

## Error Handling

The system gracefully handles errors:

1. **Import Error**: Returns error if faster-whisper not installed
2. **Transcription Error**: Returns fallback error message
3. **Empty Audio**: Returns low confidence (0.0)
4. **Unsupported Format**: Automatic conversion if possible

## Confidence Scoring

Confidence scores are calculated from:
- **Segment-level log probabilities**: Whisper provides per-segment confidence
- **Normalization**: Convert log probabilities to 0-1 range
- **Aggregation**: Average across all segments

**Interpretation**:
- **> 0.8**: High confidence - very accurate transcription
- **0.5-0.8**: Medium confidence - generally accurate
- **< 0.5**: Low confidence - may need manual review

## Monitoring

### Logs

Structured logs track transcription events:

```json
{
  "event": "audio_transcribed",
  "text_length": 76,
  "confidence": 0.73,
  "language": "en",
  "segments": 1,
  "level": "info",
  "timestamp": "2025-11-07T00:28:36.728741Z"
}
```

### Metrics

Key metrics to monitor:
- **Transcription success rate**: % of successful transcriptions
- **Average confidence**: Mean confidence score
- **Processing time**: Time to transcribe
- **Error rate**: % of failed transcriptions

## Troubleshooting

### Issue: "faster-whisper not installed"

**Solution**:
```bash
pip install faster-whisper
```

### Issue: "Audio transcription failed"

**Possible causes**:
1. Unsupported audio format
2. Corrupted audio file
3. Audio too long (> 5 minutes)
4. Memory issues

**Solution**:
- Check audio format (use WAV for best compatibility)
- Verify file is not corrupted
- Split long audio into chunks
- Increase available memory

### Issue: Slow transcription

**Solutions**:
1. Use smaller model (tiny or base)
2. Enable GPU acceleration
3. Reduce audio quality before transcription
4. Process audio asynchronously

### Issue: Low accuracy

**Solutions**:
1. Upgrade to larger model (small, medium, or large-v2)
2. Improve audio quality (reduce noise)
3. Use clearer speech
4. Check language setting

## Future Enhancements

Planned improvements:
1. **Streaming transcription**: Real-time processing
2. **Speaker diarization**: Multiple speakers
3. **Noise reduction**: Better handling of background noise
4. **Multi-language**: Support for Spanish, Chinese, etc.
5. **Custom vocabulary**: Seattle-specific terms and locations

## Dependencies

- **faster-whisper** (1.2.1+): Main transcription engine
- **torch** (2.9.0+): PyTorch for model inference
- **numpy**: Array operations
- **librosa** (optional): Audio preprocessing

## Resources

- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [CTranslate2](https://github.com/OpenNMT/CTranslate2)

## Test Results

Latest test results (2025-11-07):

```
Test Audio: "There is a large pothole on Fifth Avenue near Pine Street that needs repair."
Transcribed: "There is a large pothole on Fifth Avenue near Pine Street that needs repair."
Confidence: 73.34%
Duration: 5.28 seconds
Processing Time: ~4 seconds
Status: ✅ Success
```

**Accuracy**: 100% word accuracy on test case
