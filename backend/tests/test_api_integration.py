"""
API Integration Tests
Tests the full API endpoints end-to-end
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import io
from pathlib import Path

client = TestClient(app)


class TestAnalyzeEndpoint:
    """Integration tests for /api/v1/recordings/analyze"""

    def test_analyze_endpoint_success(self, sample_audio_path):
        """Test successful analysis with valid audio"""
        with open(sample_audio_path, "rb") as f:
            response = client.post(
                "/api/v1/recordings/analyze",
                data={
                    "user_id": "test-user-123",
                    "surah": 1,
                    "ayah": 1,
                    "mode": "short",
                },
                files={"audio_file": ("test.wav", f, "audio/wav")},
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "request_id" in data
        assert "matched_ayah" in data
        assert "errors" in data
        assert "overall_score" in data
        assert "recommendation" in data

        # Verify matched_ayah structure
        assert "surah" in data["matched_ayah"]
        assert "ayah" in data["matched_ayah"]
        assert "confidence" in data["matched_ayah"]

    def test_analyze_endpoint_invalid_file_type(self):
        """Test with unsupported file type"""
        fake_file = io.BytesIO(b"not an audio file")

        response = client.post(
            "/api/v1/recordings/analyze",
            data={"user_id": "test-user", "surah": 1, "ayah": 1},
            files={"audio_file": ("test.txt", fake_file, "text/plain")},
        )

        assert response.status_code == 400
        assert "Unsupported audio format" in response.json()["detail"]

    def test_analyze_endpoint_invalid_surah(self, sample_audio_path):
        """Test with invalid surah number"""
        with open(sample_audio_path, "rb") as f:
            response = client.post(
                "/api/v1/recordings/analyze",
                data={"user_id": "test-user", "surah": 200, "ayah": 1},
                files={"audio_file": ("test.wav", f, "audio/wav")},
            )

        assert response.status_code == 400
        assert "Surah must be between 1 and 114" in response.json()["detail"]

    def test_analyze_endpoint_missing_user_id(self, sample_audio_path):
        """Test without user_id"""
        with open(sample_audio_path, "rb") as f:
            response = client.post(
                "/api/v1/recordings/analyze",
                data={"surah": 1, "ayah": 1},
                files={"audio_file": ("test.wav", f, "audio/wav")},
            )

        assert response.status_code == 422  # Validation error


class TestQuickAnalyzeEndpoint:
    """Integration tests for /api/v1/recordings/analyze/quick"""

    def test_quick_analyze_success(self, sample_audio_path):
        """Test quick analyze with valid input"""
        with open(sample_audio_path, "rb") as f:
            response = client.post(
                "/api/v1/recordings/analyze/quick",
                data={
                    "user_id": "test-user",
                    "surah": 1,
                    "ayah": 1,
                    "target_word_index": 0,
                    "error_type": "substituted_letter",
                },
                files={"audio_file": ("test.wav", f, "audio/wav")},
            )

        assert response.status_code == 200
        data = response.json()

        assert "passed" in data
        assert "confidence" in data
        assert "feedback" in data
        assert "target_word" in data
        assert isinstance(data["passed"], bool)
        assert 0.0 <= data["confidence"] <= 1.0

    def test_quick_analyze_invalid_word_index(self, sample_audio_path):
        """Test with invalid word index"""
        with open(sample_audio_path, "rb") as f:
            response = client.post(
                "/api/v1/recordings/analyze/quick",
                data={
                    "user_id": "test-user",
                    "surah": 1,
                    "ayah": 1,
                    "target_word_index": 999,
                    "error_type": "substituted_letter",
                },
                files={"audio_file": ("test.wav", f, "audio/wav")},
            )

        assert response.status_code == 400


class TestCorrectionEndpoints:
    """Integration tests for correction endpoints"""

    def test_get_correction_audio(self):
        """Test getting correction audio"""
        response = client.get("/api/v1/correction/audio/qa_01")

        # Should return 200 or 404 depending on if sample exists
        assert response.status_code in [200, 404]

    def test_list_corrections(self):
        """Test listing available corrections"""
        response = client.get("/api/v1/correction/list")

        assert response.status_code == 200
        data = response.json()
        assert "corrections" in data


class TestFeedbackEndpoints:
    """Integration tests for feedback/review endpoints"""

    def test_submit_review(self):
        """Test submitting a review"""
        review_data = {
            "recording_id": "test-recording-123",
            "reviewer_id": "reviewer-456",
            "error_reviews": [
                {
                    "error_index": 0,
                    "is_correct": True,
                    "actual_error_type": None,
                    "notes": "Looks good",
                }
            ],
            "overall_assessment": "correct",
            "additional_errors": None,
            "notes": "Clear recording",
        }

        response = client.post("/api/v1/feedback/review", json=review_data)

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_get_review_queue(self):
        """Test getting review queue"""
        response = client.get(
            "/api/v1/feedback/queue?reviewer_id=test-reviewer&limit=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert "queue" in data
        assert "total_pending" in data


class TestHealthEndpoints:
    """Integration tests for health check endpoints"""

    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_ready_check(self):
        """Test readiness check"""
        response = client.get("/ready")

        # May be 200 or 503 depending on dependencies
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
