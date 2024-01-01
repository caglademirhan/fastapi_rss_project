# tests/test_main.py
from fastapi.testclient import TestClient
from main import app, DATABASE_URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from unittest import mock
import pytest

client = TestClient(app)

# Function to create a new database session for testing
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the dependency for the database session
app.dependency_overrides[app.get_db] = override_get_db

def test_parse_rss_success(mocker):
    # Test parsing an RSS feed successfully
    url = "https://example.com/rss-feed"
    mocker.patch("feedparser.parse", return_value={"entries": [{"title": "Test Title", "summary": "Test Description"}]})
    
    response = client.post("/parse_rss", json={"url": url})
    assert response.status_code == 200
    assert response.json()["titles"] == ["Test Title"]
    assert response.json()["descriptions"] == ["Test Description"]

def test_parse_rss_cached():
    # Test parsing an RSS feed from the cache
    url = "https://cachedrss.com/feed"
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    db.execute("INSERT INTO articles (title, description, url, created_at) VALUES ('Cached Title', 'Cached Description', :url, :created_at)",
               {"url": url, "created_at": datetime.utcnow() - timedelta(minutes=5)})  # parsed 5 minutes ago
    db.commit()
    db.close()

    response = client.post("/parse_rss", json={"url": url})
    assert response.status_code == 200
    assert response.json()["titles"] == ["Cached Title"]
    assert response.json()["descriptions"] == ["Cached Description"]

def test_parse_rss_invalid_url():
    # Test parsing an invalid RSS feed URL
    url = "invalid_url"
    response = client.post("/parse_rss", json={"url": url})
    assert response.status_code == 422  # Unprocessable Entity
    assert "detail" in response.json()

def test_token_endpoint_success(mocker):
    # Test the /token endpoint with a valid Auth0 authorization code
    mocker.patch("main.oauth2_scheme.token_request", return_value={"access_token": "mocked_access_token", "token_type": "bearer"})
    mocker.patch("main.jwt.decode", return_value={"sub": "mocked_user_id"})
    
    response = client.post("/token", data={"code": "valid_code", "state": "valid_state"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()

def test_token_endpoint_invalid_code(mocker):
    # Test the /token endpoint with an invalid Auth0 authorization code
    mocker.patch("main.oauth2_scheme.token_request", side_effect=HTTPException(status_code=401, detail="Unauthorized"))
    
    response = client.post("/token", data={"code": "invalid_code", "state": "valid_state"})
    assert response.status_code == 401  # Unauthorized
    assert "detail" in response.json()

def test_token_endpoint_missing_code():
    # Test the /token endpoint without providing an Auth0 authorization code
    response = client.post("/token", data={"state": "valid_state"})
    assert response.status_code == 422  # Unprocessable Entity
    assert "detail" in response.json()

