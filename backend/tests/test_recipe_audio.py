"""Tests for pre-recorded recipe audio upload and serving (Phase 2.3).

Tests:
- Upload audio file for a recipe
- Serve pre-recorded audio file
- 404 for non-existent recipe or audio
"""

import io
from pathlib import Path
from unittest.mock import patch

import pytest
from tests.conftest import make_recipe_orm


class TestRecipeAudioUpload:
    """Tests for POST /api/recipes/{id}/audio — upload pre-recorded audio."""

    def test_upload_audio_file(self, client, db_session, tmp_path):
        """Should upload and store an audio file for a recipe."""
        recipe = make_recipe_orm(db_session, id="sambar", name="Sambar")

        fake_audio = io.BytesIO(b"fake mp3 audio content")

        with patch("app.routers.voice.settings") as mock_settings:
            mock_settings.AUDIO_DIR = tmp_path
            resp = client.post(
                f"/api/recipes/{recipe.id}/audio",
                files={"audio_file": ("sambar_instructions.mp3", fake_audio, "audio/mpeg")},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["recipe_id"] == "sambar"
        assert "audio_url" in data
        assert "sambar" in data["audio_url"]

    def test_upload_audio_404_for_missing_recipe(self, client):
        """Should return 404 for non-existent recipe."""
        fake_audio = io.BytesIO(b"fake mp3 audio content")
        resp = client.post(
            "/api/recipes/nonexistent/audio",
            files={"audio_file": ("test.mp3", fake_audio, "audio/mpeg")},
        )
        assert resp.status_code == 404


class TestRecipeAudioServing:
    """Tests for GET /api/recipes/{id}/audio — serve pre-recorded audio."""

    def test_serve_recipe_audio(self, client, db_session, tmp_path):
        """Should serve a pre-recorded audio file for a recipe."""
        recipe = make_recipe_orm(db_session, id="sambar", name="Sambar")

        # Create a fake audio file
        audio_dir = tmp_path / "recipes"
        audio_dir.mkdir(parents=True)
        audio_file = audio_dir / "sambar.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        # Set the recipe audio URL
        recipe.recipe_audio_url = f"/api/audio/recipes/sambar.mp3"
        db_session.commit()

        with patch("app.routers.voice.settings") as mock_settings:
            mock_settings.AUDIO_DIR = tmp_path
            resp = client.get(f"/api/recipes/{recipe.id}/audio")

        assert resp.status_code == 200

    def test_404_when_no_audio(self, client, db_session):
        """Should return 404 when recipe has no audio."""
        recipe = make_recipe_orm(db_session, id="sambar", name="Sambar")
        resp = client.get(f"/api/recipes/{recipe.id}/audio")
        assert resp.status_code == 404

    def test_404_for_missing_recipe(self, client):
        """Should return 404 for non-existent recipe."""
        resp = client.get("/api/recipes/nonexistent/audio")
        assert resp.status_code == 404
