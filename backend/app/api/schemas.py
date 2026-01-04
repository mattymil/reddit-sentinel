"""Pydantic schemas for API request/response models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Classification(str, Enum):
    """Bot classification labels."""

    LIKELY_BOT = "likely_bot"
    SUSPICIOUS = "suspicious"
    PROBABLY_HUMAN = "probably_human"
    UNKNOWN = "unknown"


class ContributingFactor(BaseModel):
    """A factor contributing to the bot score."""

    factor: str = Field(..., description="Name of the feature")
    contribution: float = Field(..., description="Contribution to score (0-1)")
    value: float | int | bool = Field(..., description="Raw feature value")


class TimezoneEstimate(BaseModel):
    """Estimated timezone from posting patterns."""

    likely_offset: str = Field(..., description="Estimated UTC offset")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in estimate")
    peak_hours_utc: list[int] = Field(
        default_factory=list, description="Peak posting hours in UTC"
    )


class ScoreResponse(BaseModel):
    """Response for a single user score."""

    username: str
    bot_probability: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    classification: Classification
    contributing_factors: list[ContributingFactor] = Field(default_factory=list)
    timezone_estimate: TimezoneEstimate | None = None
    analyzed_at: datetime
    cached: bool = False
    cache_expires_at: datetime | None = None


class BatchRequest(BaseModel):
    """Request for batch analysis."""

    usernames: list[str] = Field(..., min_length=1, max_length=50)
    force_refresh: bool = False


class BatchResultStatus(str, Enum):
    """Status of a batch result item."""

    COMPLETED = "completed"
    ERROR = "error"
    CACHED = "cached"


class BatchResultItem(BaseModel):
    """Single item in batch response."""

    username: str
    status: BatchResultStatus
    score: ScoreResponse | None = None
    error: str | None = None


class BatchResponse(BaseModel):
    """Response for batch analysis."""

    results: list[BatchResultItem]
    processing_time_ms: int


class FeedbackType(str, Enum):
    """Type of user feedback."""

    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    CONFIRMED_BOT = "confirmed_bot"
    CONFIRMED_HUMAN = "confirmed_human"


class FeedbackRequest(BaseModel):
    """Request to submit feedback."""

    username: str
    feedback_type: FeedbackType
    notes: str | None = None


class FeedbackResponse(BaseModel):
    """Response for feedback submission."""

    success: bool
    message: str


class HealthResponse(BaseModel):
    """Response for health check."""

    status: str
    redis_connected: bool
    model_loaded: bool
    version: str


class StatsResponse(BaseModel):
    """Response for system statistics."""

    total_accounts_analyzed: int
    cache_hit_rate: float
    model_version: str
    uptime_seconds: int
    feedback_counts: dict[str, int] = Field(default_factory=dict)
