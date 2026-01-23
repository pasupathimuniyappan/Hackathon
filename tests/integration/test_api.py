import pytest
import httpx
from fastapi.testclient import TestClient
from src.server import app


@pytest.fixture
def client():
    return TestClient(app)


class TestAPIEndpoints:
    def test_health_check(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
    
    def test_analyze_poor_prompt(self, client):
        """Test analysis of poor quality prompt."""
        response = client.post(
            "/api/prompt/analyze",
            json={"text": "analyze data", "use_llm": False}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["quality_score"] < 50
        assert len(data["issues"]) >= 2
    
    def test_analyze_good_prompt(self, client):
        """Test analysis of good quality prompt."""
        good_prompt = (
            "You are a data analyst. Analyze the sales dataset focusing on: "
            "1) Revenue trends 2) Top products. Format as bullet points."
        )
        
        response = client.post(
            "/api/prompt/analyze",
            json={"text": good_prompt, "use_llm": False}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["quality_score"] >= 70
        assert len(data["issues"]) <= 1
    
    def test_optimize_prompt(self, client):
        """Test prompt optimization."""
        response = client.post(
            "/api/prompt/optimize",
            json={"text": "analyze data", "focus": "all", "level": "balanced"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["quality_improvement"] > 0
        assert data["after_score"] > data["before_score"]
        assert len(data["optimized_prompt"]) > len("analyze data")
    
    def test_rate_limiting(self, client):
        """Test basic rate limiting (requires Redis)."""
        for _ in range(5):
            response = client.post("/api/prompt/analyze", json={"text": "test"})
            assert response.status_code == 200
    
    def test_validation_errors(self, client):
        """Test input validation."""
        # Empty text
        response = client.post("/api/prompt/analyze", json={"text": ""})
        assert response.status_code == 422
        
        # Too long
        long_text = "a" * 6000
        response = client.post("/api/prompt/analyze", json={"text": long_text})
        assert response.status_code == 400
