"""Azure TTS Service — Text-to-Speech using Azure Cognitive Services.

Converts Hindi text to natural-sounding speech audio (MP3).
Voice: hi-IN-KavyaNeural (Hindi female neural voice).

Graceful fallback: if TTS fails, callers should fall back to displaying
the Hindi script text for manual recording.
"""

import asyncio
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def _synthesize_blocking(
    text: str,
    output_path: Path,
    voice_name: str,
) -> Path:
    """Synchronous TTS synthesis — runs in a thread pool to avoid blocking the event loop."""
    # Lazy import — azure-cognitiveservices-speech may not be installed in test env
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError:
        raise RuntimeError(
            "azure-cognitiveservices-speech package is not installed. "
            "Install it with: pip install azure-cognitiveservices-speech"
        )

    # Configure Azure Speech
    speech_config = speechsdk.SpeechConfig(
        subscription=settings.AZURE_SPEECH_KEY,
        region=settings.AZURE_SPEECH_REGION,
    )
    speech_config.speech_synthesis_voice_name = voice_name
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
    )

    # Use file output
    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    # Synchronous SDK call
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        logger.info(f"TTS audio saved to {output_path}")
        return output_path
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        error_msg = f"TTS canceled: {cancellation.reason}"
        if cancellation.error_details:
            error_msg += f" — {cancellation.error_details}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    else:
        raise RuntimeError(f"TTS failed with reason: {result.reason}")


async def synthesize_speech(
    text: str,
    filename: str,
    voice_name: str = "hi-IN-KavyaNeural",
) -> Path:
    """Synthesize Hindi text to speech using Azure Cognitive Services.

    Args:
        text: Hindi text to convert to speech.
        filename: Output filename (e.g. "brief_1.mp3").
        voice_name: Azure TTS voice name.

    Returns:
        Path to the generated audio file.

    Raises:
        RuntimeError: If TTS synthesis fails.
        ValueError: If Azure Speech credentials are not configured.
    """
    if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
        raise ValueError(
            "Azure Speech credentials not configured. "
            "Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in .env"
        )

    # Ensure audio directory exists
    audio_dir = settings.AUDIO_DIR
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / filename

    # Run blocking SDK call in thread pool so we don't stall the async event loop
    return await asyncio.to_thread(
        _synthesize_blocking, text, output_path, voice_name
    )
