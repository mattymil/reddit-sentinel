"""Pytest fixtures for RedditSentinel tests."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import fakeredis
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def redis_client():
    """Provide a fake Redis client for testing."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def mock_reddit():
    """Provide a mock PRAW Reddit instance."""
    with patch("praw.Reddit") as mock:
        reddit = MagicMock()
        mock.return_value = reddit
        yield reddit


@pytest.fixture
def sample_redditor():
    """Provide a sample Redditor object for testing."""
    redditor = MagicMock()
    redditor.name = "TestUser123"
    redditor.created_utc = datetime(2023, 1, 1, tzinfo=UTC).timestamp()
    redditor.link_karma = 1000
    redditor.comment_karma = 500
    redditor.has_verified_email = True
    redditor.is_gold = False
    redditor.trophies.return_value = [MagicMock(), MagicMock()]  # 2 trophies
    return redditor


@pytest.fixture
def sample_submissions():
    """Provide sample submission objects for testing."""
    submissions = []
    for i in range(5):
        sub = MagicMock()
        sub.title = f"Test Post {i}"
        sub.selftext = f"This is the content of test post {i}."
        sub.subreddit.display_name = ["funny", "pics", "news", "funny", "pics"][i]
        sub.created_utc = datetime(2024, 1, i + 1, 12, 0, tzinfo=UTC).timestamp()
        sub.score = 100 + i * 10
        submissions.append(sub)
    return submissions


@pytest.fixture
def sample_comments():
    """Provide sample comment objects for testing."""
    comments = []
    for i in range(10):
        comment = MagicMock()
        comment.body = f"This is test comment number {i}. It has some words in it."
        comment.subreddit.display_name = ["funny", "pics", "news"][i % 3]
        comment.created_utc = datetime(2024, 1, 1, i, 0, tzinfo=UTC).timestamp()
        comment.score = 10 + i
        comments.append(comment)
    return comments


@pytest.fixture
def bot_like_redditor():
    """Provide a Redditor that exhibits bot-like characteristics."""
    redditor = MagicMock()
    redditor.name = "SuspiciousBot999"
    redditor.created_utc = datetime(2024, 12, 1, tzinfo=UTC).timestamp()  # Very new
    redditor.link_karma = 50000  # Suspiciously high for new account
    redditor.comment_karma = 100
    redditor.has_verified_email = False
    redditor.is_gold = False
    redditor.trophies.return_value = []  # No trophies
    return redditor


@pytest.fixture
def bot_like_comments():
    """Provide comments with bot-like linguistic patterns."""
    comments = []
    texts = [
        "Kindly check this out, it peaked my interest!",
        "I'm loosing my mind over this leek in the system.",
        "Please do the needful and revert back to me.",
        "This is so helpful! Same to you my friend.",
        "I will prepone the meeting and discuss about it.",
    ]
    for i, text in enumerate(texts):
        comment = MagicMock()
        comment.body = text
        comment.subreddit.display_name = "spam"  # Low diversity
        comment.created_utc = datetime(
            2024, 1, 1, 3, i, tzinfo=UTC
        ).timestamp()  # Same hour
        comment.score = 1
        comments.append(comment)
    return comments


@pytest.fixture
def app_client(redis_client, mock_reddit):
    """Provide a test client for the FastAPI app."""
    # Import here to avoid circular imports and allow mocking
    with patch("app.main.get_redis_client", return_value=redis_client):
        from app.main import app

        with TestClient(app) as client:
            yield client


@pytest.fixture
def sample_features():
    """Provide a sample feature dict for testing the scorer."""
    return {
        # Account features
        "account_age_days": 365,
        "total_karma": 1500,
        "post_karma_ratio": 0.67,
        "is_verified_email": True,
        "has_premium": False,
        "trophy_count": 2,
        "karma_per_day": 4.1,
        # Behavioral features
        "posts_per_day_avg": 0.5,
        "comments_per_day_avg": 2.0,
        "unique_subreddits": 15,
        "subreddit_entropy": 2.8,
        "posting_hour_entropy": 3.2,
        "posting_hour_mode": 14,
        "active_hours_spread": 12,
        "burst_score": 0.2,
        "weekend_ratio": 0.3,
        # Linguistic features
        "avg_word_count": 25.0,
        "vocabulary_richness": 0.65,
        "avg_word_length": 4.5,
        "avg_sentence_length": 12.0,
        "phonetic_error_score": 0.0,
        "article_error_rate": 0.0,
        "formality_score": 0.1,
        "emoji_density": 0.02,
        "question_ratio": 0.15,
    }


@pytest.fixture
def bot_like_features():
    """Provide features that should trigger high bot score."""
    return {
        # Account features - new account with suspicious karma
        "account_age_days": 15,
        "total_karma": 10000,
        "post_karma_ratio": 0.95,
        "is_verified_email": False,
        "has_premium": False,
        "trophy_count": 0,
        "karma_per_day": 666.7,
        # Behavioral features - low entropy, high activity
        "posts_per_day_avg": 15.0,
        "comments_per_day_avg": 50.0,
        "unique_subreddits": 2,
        "subreddit_entropy": 0.3,
        "posting_hour_entropy": 0.5,
        "posting_hour_mode": 3,
        "active_hours_spread": 4,
        "burst_score": 0.9,
        "weekend_ratio": 0.1,
        # Linguistic features - phonetic errors
        "avg_word_count": 10.0,
        "vocabulary_richness": 0.3,
        "avg_word_length": 4.0,
        "avg_sentence_length": 8.0,
        "phonetic_error_score": 0.6,
        "article_error_rate": 0.3,
        "formality_score": 0.7,
        "emoji_density": 0.0,
        "question_ratio": 0.0,
    }
