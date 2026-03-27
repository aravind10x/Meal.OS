"""Tests for the Azure TTS service (Phase 2.2).

Tests:
- TTS synthesis (mocked SDK)
- Error handling (missing credentials, synthesis failure)
- Voice audio API endpoint
- Audio file serving endpoint (including path traversal hardening)
"""

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.meal_plan import MealPlan


def _make_mock_speechsdk():
    """Create a fully configured mock Azure Speech SDK with concrete reason values."""
    mock = MagicMock()
    mock.ResultReason.SynthesizingAudioCompleted = "COMPLETED"
    mock.ResultReason.Canceled = "CANCELED"
    mock.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3 = "mp3_format"
    return mock


def _patch_azure_sdk(mock_speechsdk):
    """Return a patch.dict that mocks the entire azure.cognitiveservices.speech import chain."""
    # Build a linked hierarchy so attribute access also resolves correctly
    mock_cog = MagicMock()
    mock_cog.speech = mock_speechsdk
    mock_azure = MagicMock()
    mock_azure.cognitiveservices = mock_cog
    mock_azure.cognitiveservices.speech = mock_speechsdk
    return patch.dict("sys.modules", {
        "azure": mock_azure,
        "azure.cognitiveservices": mock_cog,
        "azure.cognitiveservices.speech": mock_speechsdk,
    })


# ---------------------------------------------------------------------------
# TTS Service unit tests (mock Azure SDK)
# ---------------------------------------------------------------------------


class TestTTSService:
    """Tests for synthesize_speech with mocked Azure SDK."""

    @pytest.mark.asyncio
    async def test_raises_if_no_credentials(self):
        """Should raise ValueError when Azure Speech credentials are missing."""
        with patch("app.services.tts.settings") as mock_settings:
            mock_settings.AZURE_SPEECH_KEY = ""
            mock_settings.AZURE_SPEECH_REGION = ""

            from app.services.tts import synthesize_speech

            with pytest.raises(ValueError, match="credentials not configured"):
                await synthesize_speech("Test text", "test.mp3")

    @pytest.mark.asyncio
    async def test_successful_synthesis(self, tmp_path):
        """Should call the Azure Speech SDK synthesizer on successful synthesis."""
        mock_speechsdk = _make_mock_speechsdk()

        # Mock the result — mark as completed
        mock_result = MagicMock()
        mock_result.reason = "COMPLETED"

        # Mock the synthesizer
        mock_synthesizer = MagicMock()
        mock_async_result = MagicMock()
        mock_async_result.get.return_value = mock_result
        mock_synthesizer.speak_text_async.return_value = mock_async_result

        mock_speechsdk.SpeechSynthesizer.return_value = mock_synthesizer
        mock_speechsdk.SpeechConfig.return_value = MagicMock()
        mock_speechsdk.audio.AudioOutputConfig.return_value = MagicMock()

        with patch("app.services.tts.settings") as mock_settings, \
             _patch_azure_sdk(mock_speechsdk):
            mock_settings.AZURE_SPEECH_KEY = "test-key"
            mock_settings.AZURE_SPEECH_REGION = "eastus"
            mock_settings.AUDIO_DIR = tmp_path

            from app.services.tts import synthesize_speech
            result = await synthesize_speech(
                "नमस्ते! कल के लिए समबार बनानी है।", "test_brief.mp3"
            )

        mock_synthesizer.speak_text_async.assert_called_once()
        assert result == tmp_path / "test_brief.mp3"

    @pytest.mark.asyncio
    async def test_raises_on_cancellation(self, tmp_path):
        """Should raise RuntimeError when synthesis is canceled."""
        mock_speechsdk = _make_mock_speechsdk()

        mock_result = MagicMock()
        mock_result.reason = "CANCELED"
        mock_result.cancellation_details.reason = "Error"
        mock_result.cancellation_details.error_details = "Invalid key"

        mock_synthesizer = MagicMock()
        mock_async_result = MagicMock()
        mock_async_result.get.return_value = mock_result
        mock_synthesizer.speak_text_async.return_value = mock_async_result

        mock_speechsdk.SpeechSynthesizer.return_value = mock_synthesizer
        mock_speechsdk.SpeechConfig.return_value = MagicMock()
        mock_speechsdk.audio.AudioOutputConfig.return_value = MagicMock()

        with patch("app.services.tts.settings") as mock_settings, \
             _patch_azure_sdk(mock_speechsdk):
            mock_settings.AZURE_SPEECH_KEY = "test-key"
            mock_settings.AZURE_SPEECH_REGION = "eastus"
            mock_settings.AUDIO_DIR = tmp_path

            from app.services.tts import synthesize_speech

            with pytest.raises(RuntimeError, match="TTS canceled"):
                await synthesize_speech("Test", "test.mp3")


# ---------------------------------------------------------------------------
# Voice Audio API tests
# ---------------------------------------------------------------------------


class TestVoiceAudioAPI:
    """Tests for GET /api/voice-audio/{plan_id}."""

    def _create_approved_plan(self, db_session, **overrides) -> MealPlan:
        defaults = {
            "plan_date": date.today() + timedelta(days=1),
            "status": "approved",
            "template_id": "south_indian",
            "cuisine": "South Indian",
            "egg_style": "omelette",
            "roti_count": "standard batch",
            "kid_notes": "Less spicy",
            "rationale": "Test",
        }
        defaults.update(overrides)

        plan = MealPlan(**defaults)
        plan.set_dishes([
            {"recipe_id": "test_dish", "role": "main", "name": "Test Dish"},
        ])
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        return plan

    def test_returns_cached_audio(self, client, db_session):
        """If audio URL already exists, return it directly."""
        plan = self._create_approved_plan(db_session)
        plan.voice_script_text = "Hindi script text"
        plan.voice_audio_url = "/api/audio/brief_1.mp3"
        db_session.commit()

        resp = client.get(f"/api/voice-audio/{plan.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["audio_url"] == "/api/audio/brief_1.mp3"
        assert data["script_text"] == "Hindi script text"

    def test_404_for_nonexistent_plan(self, client):
        resp = client.get("/api/voice-audio/99999")
        assert resp.status_code == 404

    def test_400_for_draft_plan(self, client, db_session):
        plan = self._create_approved_plan(db_session, status="draft")
        resp = client.get(f"/api/voice-audio/{plan.id}")
        assert resp.status_code == 400

    @patch("app.routers.voice.synthesize_speech", new_callable=AsyncMock)
    @patch("app.routers.voice.generate_voice_script", new_callable=AsyncMock)
    def test_generates_script_and_audio(self, mock_gen, mock_tts, client, db_session, tmp_path):
        """Should generate script + audio when neither is cached."""
        mock_gen.return_value = "Hindi script text"
        mock_tts.return_value = tmp_path / "brief_test.mp3"

        plan = self._create_approved_plan(db_session)
        resp = client.get(f"/api/voice-audio/{plan.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["audio_url"] is not None
        assert data["script_text"] == "Hindi script text"

    @patch("app.routers.voice.synthesize_speech", new_callable=AsyncMock)
    def test_tts_failure_returns_fallback(self, mock_tts, client, db_session):
        """If TTS fails, should return script text with error message."""
        mock_tts.side_effect = RuntimeError("TTS failed")

        plan = self._create_approved_plan(db_session)
        plan.voice_script_text = "Existing Hindi script"
        db_session.commit()

        resp = client.get(f"/api/voice-audio/{plan.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["audio_url"] is None
        assert data["script_text"] == "Existing Hindi script"
        assert "tts_error" in data


# ---------------------------------------------------------------------------
# Audio file serving tests (including path traversal hardening)
# ---------------------------------------------------------------------------


class TestAudioServing:
    """Tests for GET /api/audio/{filename}."""

    def test_404_for_missing_audio_file(self, client):
        resp = client.get("/api/audio/nonexistent.mp3")
        assert resp.status_code == 404

    def test_prevents_directory_traversal(self, client):
        """Should sanitize filename to prevent path traversal."""
        resp = client.get("/api/audio/../../etc/passwd")
        assert resp.status_code == 404

    def test_prevents_sibling_prefix_traversal(self, client):
        """Should block paths that share a prefix with the audio dir but escape it."""
        # e.g. audio_files_evil/secret.mp3 — string startswith would pass, is_relative_to won't
        resp = client.get("/api/audio/../audio_files_evil/secret.mp3")
        assert resp.status_code == 404

    def test_serves_valid_audio_file(self, client, tmp_path):
        """Should serve a file that exists within the audio directory."""
        with patch("app.routers.voice.settings") as mock_settings:
            mock_settings.AUDIO_DIR = tmp_path
            # Create a test audio file
            audio_file = tmp_path / "test_serve.mp3"
            audio_file.write_bytes(b"fake audio data")

            resp = client.get("/api/audio/test_serve.mp3")
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "audio/mpeg"
