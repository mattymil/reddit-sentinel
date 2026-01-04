# RedditSentinel - Reddit Bot Detection & Filtering System

## Project Summary

Create a GitHub repo called `reddit-sentinel` - a personal Reddit bot detection and filtering system that uses ML to identify suspected bot accounts and filters them from my Reddit feed via a browser extension.

**This is for personal use only** - self-hosted on AWS, no multi-tenancy, no scale requirements.

## Origin Story

I noticed a pattern on Reddit where posts contain phonetic spelling errors (e.g., "leek" instead of "leak" on r/aviation) that suggest non-native English speakers who learned the language aurally. These often appear on reposted content that previously had correct spelling. This suggests foreign bot farms or human-bot operations are infiltrating Reddit for karma farming, SEO manipulation, or astroturfing.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER'S BROWSER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                 RedditSentinel Browser Extension                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │    │
│  │  │ DOM Observer │  │  Score Cache │  │    UI Modification Layer   │ │    │
│  │  │ (usernames)  │  │  (IndexedDB) │  │  (hide/flag/badge posts)   │ │    │
│  │  └──────┬───────┘  └──────▲───────┘  └────────────▲───────────────┘ │    │
│  │         │                 │                       │                  │    │
│  │         └─────────────────┴───────────────────────┘                  │    │
│  │                           │                                          │    │
│  │  ┌────────────────────────┴─────────────────────────────────────┐   │    │
│  │  │   API Client - Batch queries to backend                       │   │    │
│  │  └────────────────────────┬─────────────────────────────────────┘   │    │
│  └───────────────────────────┼──────────────────────────────────────────┘    │
└──────────────────────────────┼──────────────────────────────────────────────┘
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI on AWS)                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          API Gateway                                 │    │
│  │   POST /v1/analyze/batch  - Analyze multiple usernames              │    │
│  │   GET  /v1/score/{user}   - Get cached score for single user        │    │
│  │   POST /v1/feedback       - Report false positive/negative          │    │
│  │   GET  /v1/health         - Health check                            │    │
│  │   GET  /v1/stats          - System statistics                       │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                                 │                                            │
│         ┌───────────────────────┼───────────────────────────┐               │
│         ▼                       ▼                           ▼               │
│  ┌─────────────┐    ┌───────────────────────┐    ┌─────────────────────┐   │
│  │ Score Cache │    │   Analysis Engine     │    │  Feedback Store     │   │
│  │   (Redis)   │    │                       │    │  (for retraining)   │   │
│  │             │    │  ┌─────────────────┐  │    └─────────────────────┘   │
│  │ TTL: 48h    │    │  │ Feature         │  │                              │
│  │             │    │  │ Extractor       │  │                              │
│  └──────▲──────┘    │  └────────┬────────┘  │                              │
│         │           │           ▼           │                              │
│         │           │  ┌─────────────────┐  │                              │
│         │           │  │ ML Model        │  │                              │
│         │           │  │ (Inference)     │  │                              │
│         │           │  └────────┬────────┘  │                              │
│         │           │           ▼           │                              │
│         │           │  ┌─────────────────┐  │                              │
│         └───────────┼──│ Score Generator │  │                              │
│                     │  └─────────────────┘  │                              │
│                     └───────────────────────┘                              │
│                                 │                                            │
│  ┌──────────────────────────────┴───────────────────────────────────────┐   │
│  │                     Reddit Data Collector (PRAW)                      │   │
│  │              Respects rate limits (60 req/min), caches responses      │   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  ▼
                        ┌───────────────────┐
                        │    Reddit API     │
                        └───────────────────┘
```

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend API | Python 3.11+, FastAPI | Async support, type hints, auto-docs |
| Reddit Access | PRAW | Official Reddit API wrapper |
| Caching | Redis | Fast, simple, TTL support |
| ML Model | scikit-learn | Start simple (Random Forest), upgrade later |
| Browser Extension | Chrome Manifest V3 | Modern extension standard |
| Local Dev | Docker Compose | Easy setup with Redis |
| Production | AWS (ECS Fargate or EC2) | Matt's preferred platform |

## Directory Structure

```
reddit-sentinel/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── config.py               # Pydantic settings from environment
│   │   ├── collectors/
│   │   │   ├── __init__.py
│   │   │   └── reddit.py           # PRAW wrapper, user data collection
│   │   ├── features/
│   │   │   ├── __init__.py
│   │   │   ├── account.py          # Account metadata features
│   │   │   ├── behavioral.py       # Posting pattern features
│   │   │   ├── linguistic.py       # Text analysis features
│   │   │   └── extractor.py        # Main orchestrator
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── detector.py         # ML model wrapper
│   │   │   └── heuristic.py        # Fallback heuristic scorer
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── routes.py           # Endpoint definitions
│   │       └── schemas.py          # Pydantic request/response models
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_collectors.py
│   │   ├── test_features.py
│   │   └── test_api.py
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── pyproject.toml
├── extension/
│   ├── manifest.json               # Chrome Manifest V3
│   ├── src/
│   │   ├── background.js           # Service worker
│   │   ├── content.js              # DOM observer and modifier
│   │   ├── popup.js                # Settings popup logic
│   │   ├── api.js                  # Backend API client
│   │   └── cache.js                # IndexedDB wrapper
│   ├── popup.html
│   ├── options.html
│   ├── styles.css
│   └── icons/
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
├── training/
│   ├── data/                       # Training data (gitignored)
│   ├── notebooks/
│   │   └── exploration.ipynb       # Feature analysis
│   ├── collect_training_data.py    # Gather labeled examples
│   └── train_model.py              # Train and export model
├── infrastructure/
│   └── aws/
│       └── ecs-task-definition.json
├── .env.example
├── .gitignore
├── README.md
└── CLAUDE.md                       # This file
```

## API Specification

### Endpoints

#### `GET /v1/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "redis_connected": true,
  "model_loaded": true,
  "version": "0.1.0"
}
```

#### `GET /v1/score/{username}`
Get bot score for a single user. Returns cached result if available.

**Response:**
```json
{
  "username": "SuspiciousUser123",
  "bot_probability": 0.87,
  "confidence": 0.92,
  "classification": "likely_bot",
  "contributing_factors": [
    {"factor": "phonetic_error_score", "contribution": 0.23, "value": 0.45},
    {"factor": "account_age_days", "contribution": 0.18, "value": 12},
    {"factor": "posting_hour_entropy", "contribution": 0.15, "value": 0.34},
    {"factor": "subreddit_entropy", "contribution": 0.12, "value": 0.21}
  ],
  "timezone_estimate": {
    "likely_offset": "UTC+5:30",
    "confidence": 0.65
  },
  "analyzed_at": "2026-01-04T15:30:00Z",
  "cached": true,
  "cache_expires_at": "2026-01-06T15:30:00Z"
}
```

#### `POST /v1/analyze/batch`
Analyze multiple usernames in one request.

**Request:**
```json
{
  "usernames": ["user1", "user2", "user3"],
  "force_refresh": false
}
```

**Response:**
```json
{
  "results": [
    {
      "username": "user1",
      "status": "completed",
      "score": { /* same as single score response */ }
    },
    {
      "username": "user2",
      "status": "completed",
      "score": { /* ... */ }
    },
    {
      "username": "user3",
      "status": "error",
      "error": "User not found or suspended"
    }
  ],
  "processing_time_ms": 1234
}
```

#### `POST /v1/feedback`
Submit feedback on a score (for future model retraining).

**Request:**
```json
{
  "username": "FlaggedUser",
  "feedback_type": "false_positive",
  "notes": "This is a legitimate 5-year-old account"
}
```

#### `GET /v1/stats`
System statistics.

**Response:**
```json
{
  "total_accounts_analyzed": 15234,
  "cache_hit_rate": 0.73,
  "model_version": "0.1.0",
  "uptime_seconds": 86400
}
```

## Feature Extraction Specification

### A. Account Metadata Features

| Feature | Type | Description | Bot Signal |
|---------|------|-------------|------------|
| `account_age_days` | int | Days since account creation | Young accounts (< 30 days) more suspicious |
| `total_karma` | int | Combined post + comment karma | Very high or very low can be suspicious |
| `post_karma_ratio` | float | post_karma / total_karma | Heavily skewed ratios suspicious |
| `is_verified_email` | bool | Email verification status | Bots often skip verification |
| `has_premium` | bool | Reddit Premium subscriber | Bots rarely pay for premium |
| `trophy_count` | int | Number of Reddit trophies | Legitimate users accumulate these over time |
| `karma_per_day` | float | total_karma / account_age_days | Abnormally high = suspicious |

### B. Behavioral Features

| Feature | Type | Description | Bot Signal |
|---------|------|-------------|------------|
| `posts_per_day_avg` | float | Average posts per day | > 10/day suspicious |
| `comments_per_day_avg` | float | Average comments per day | Very high = suspicious |
| `unique_subreddits` | int | Distinct subreddits posted/commented in | Very low diversity = suspicious |
| `subreddit_entropy` | float | Shannon entropy of subreddit distribution | Low entropy = focused bot behavior |
| `posting_hour_entropy` | float | Shannon entropy of posting hours (UTC) | Low entropy = automated posting |
| `posting_hour_mode` | int | Most common posting hour (0-23 UTC) | Used for timezone inference |
| `active_hours_spread` | int | Hours between earliest and latest typical posting | Narrow spread = single timezone |
| `burst_score` | float | Measure of posting in bursts vs spread out | High burst = bot behavior |
| `weekend_ratio` | float | Weekend posts / total posts | Unusual ratios can indicate bots |

### C. Linguistic Features

| Feature | Type | Description | Bot Signal |
|---------|------|-------------|------------|
| `avg_word_count` | float | Average words per post/comment | Very short averages suspicious |
| `vocabulary_richness` | float | Unique words / total words | Low richness = repetitive bot |
| `avg_word_length` | float | Average characters per word | Unusual values suspicious |
| `avg_sentence_length` | float | Average words per sentence | Very uniform = bot-like |
| `phonetic_error_score` | float | Detected phonetic spelling errors per 100 words | **KEY FEATURE** - High = non-native pattern |
| `article_error_rate` | float | a/an/the usage errors per 100 words | Common non-native marker |
| `formality_score` | float | Detection of overly formal constructions | "Kindly", "do the needful" patterns |
| `emoji_density` | float | Emojis per 100 characters | Cultural usage patterns differ |
| `question_ratio` | float | Questions / total sentences | Engagement bait patterns |

### D. Phonetic Error Patterns

These are the specific patterns that triggered this project. Non-native English speakers who learned aurally make characteristic errors:

```python
PHONETIC_ERROR_PATTERNS = [
    # Homophones that native speakers rarely confuse
    (r'\bleek\b', 'leak'),           # The original observation
    (r'\bpeak\b.*interest', 'pique'),  # "peaked my interest"
    (r'\bpeek\b.*interest', 'pique'),
    (r'\bloose\b.*(?:mind|it)', 'lose'),  # "loose my mind"
    (r'\bbrake\b.*(?:down|up)', 'break'),
    
    # Common non-native patterns
    (r'\bwich\b', 'which'),
    (r'\bwanna\b', 'want to'),        # Not an error but pattern
    (r'\bgonna\b', 'going to'),
    
    # Overly formal constructions (Indian English markers)
    (r'\bkindly\b', ''),              # "Kindly do X"
    (r'\bdo the needful\b', ''),
    (r'\brevert back\b', ''),         # "Please revert back"
    (r'\bprepone\b', ''),             # Indian English for "move earlier"
    (r'\bsame to you\b', ''),         # Response to any greeting
    
    # Article errors
    (r'\ba\s+[aeiou]\w+', ''),        # "a apple" instead of "an apple"
    (r'\ban\s+[^aeiou\s]\w+', ''),    # "an book" instead of "a book"
    
    # Preposition errors common in non-native speakers
    (r'\bdiscuss about\b', ''),       # "discuss about X"
    (r'\bexplain about\b', ''),
    (r'\bemphasize on\b', ''),
]
```

### E. Timezone Inference

Since Reddit doesn't expose location data, we infer timezone from posting patterns:

```python
def infer_timezone(posting_hours: list[int]) -> dict:
    """
    Infer likely timezone from posting hour distribution.
    
    Assumption: Users typically post during waking hours (8am - midnight local time).
    If we see a cluster of posts at UTC hours 14-22, that suggests UTC+0 to UTC+2.
    If we see posts clustered at UTC hours 2-10, that suggests UTC+8 to UTC+10.
    
    Returns:
        {
            "likely_offset": "UTC+5:30",
            "confidence": 0.65,
            "peak_hours_utc": [14, 15, 16]
        }
    """
    pass
```

## ML Model Specification

### Phase 1: Heuristic Scorer (MVP)

Start with a weighted heuristic scorer to validate the pipeline before training a real model:

```python
def heuristic_score(features: dict) -> float:
    """
    Simple weighted scoring based on suspicious signals.
    Returns 0.0 (definitely human) to 1.0 (definitely bot).
    """
    score = 0.0
    
    # Account age (newer = more suspicious)
    if features['account_age_days'] < 30:
        score += 0.20
    elif features['account_age_days'] < 90:
        score += 0.10
    
    # Phonetic errors (THE key signal)
    if features['phonetic_error_score'] > 0.5:
        score += 0.25
    elif features['phonetic_error_score'] > 0.2:
        score += 0.15
    
    # Low subreddit diversity
    if features['subreddit_entropy'] < 0.5:
        score += 0.15
    
    # Suspicious posting patterns
    if features['posting_hour_entropy'] < 1.0:
        score += 0.15
    
    # Very high activity
    if features['posts_per_day_avg'] > 10:
        score += 0.15
    
    # No trophies on older account
    if features['trophy_count'] == 0 and features['account_age_days'] > 90:
        score += 0.10
    
    return min(score, 1.0)
```

### Phase 2: Random Forest Classifier

Once we have labeled training data:

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# Train
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    random_state=42
)
model.fit(X_train, y_train)

# Export
joblib.dump(model, 'models/bot_detector.joblib')
```

### Training Data Sources

| Source | Label | How to Obtain |
|--------|-------|---------------|
| Reddit ban waves | Bot (positive) | Accounts that get suspended for manipulation |
| r/TheseFuckingAccounts | Bot (confirmed) | Community-identified bot accounts |
| Known karma farmers | Bot (confirmed) | Flagged by existing tools |
| Aged accounts with trophies | Human (negative) | Long-standing legitimate accounts |
| Verified moderators | Human (confirmed) | Active community members |
| Your own false positive feedback | Human (corrected) | Accounts you mark as incorrectly flagged |

## Browser Extension Specification

### Manifest V3

```json
{
  "manifest_version": 3,
  "name": "RedditSentinel",
  "version": "0.1.0",
  "description": "Identify and filter suspected bot accounts on Reddit",
  
  "permissions": [
    "storage",
    "activeTab"
  ],
  
  "host_permissions": [
    "https://www.reddit.com/*",
    "https://old.reddit.com/*",
    "https://new.reddit.com/*"
  ],
  
  "background": {
    "service_worker": "src/background.js"
  },
  
  "content_scripts": [
    {
      "matches": [
        "https://www.reddit.com/*",
        "https://old.reddit.com/*"
      ],
      "js": ["src/content.js"],
      "css": ["styles.css"],
      "run_at": "document_idle"
    }
  ],
  
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  
  "options_page": "options.html"
}
```

### Content Script Behavior

1. **DOM Observer**: Watch for Reddit posts loading (including infinite scroll)
2. **Username Extraction**: Parse author usernames from post elements
3. **Batch Query**: Collect usernames and query backend in batches (max 20 at a time)
4. **Cache Check**: Check IndexedDB first before API call
5. **UI Modification**: Based on score and user settings:
   - `score >= hideThreshold`: Hide/collapse/blur the post
   - `score >= flagThreshold`: Add warning badge
   - `score < flagThreshold`: Optional subtle indicator

### User Settings

```javascript
const defaultSettings = {
  // Thresholds
  hideThreshold: 0.85,      // Hide posts above this score
  flagThreshold: 0.60,      // Flag posts above this score
  
  // Display mode for hidden posts
  hideMode: 'collapse',     // 'collapse' | 'blur' | 'remove'
  
  // Visual options
  showBadgeOnAll: false,    // Show score badge on all posts
  badgePosition: 'inline',  // 'inline' | 'overlay'
  
  // Backend
  apiEndpoint: 'http://localhost:8000/v1',  // Change for production
  
  // Cache
  localCacheTTLHours: 24,
  
  // Behavior
  analyzeComments: false,   // Also check comment authors (more API calls)
};
```

## Development Phases

### Phase 1: Backend MVP
1. Set up project structure and Docker Compose
2. Implement Reddit data collector with PRAW
3. Implement feature extraction (account, behavioral, linguistic)
4. Implement heuristic scorer
5. Create FastAPI endpoints with Redis caching
6. Write basic tests

### Phase 2: Browser Extension
1. Create extension manifest and structure
2. Implement DOM observer for Reddit
3. Implement API client with batching
4. Implement IndexedDB cache
5. Implement UI modifications (hide/flag/badge)
6. Create settings popup

### Phase 3: Refinement
1. Collect training data from various sources
2. Train Random Forest model
3. Evaluate and tune model
4. Improve linguistic feature extraction
5. Add feedback mechanism
6. Polish extension UI

### Phase 4: AWS Deployment
1. Create ECS task definition or EC2 setup
2. Set up ElastiCache for Redis
3. Configure environment variables
4. Set up CloudWatch logging
5. Update extension to use production endpoint

## Environment Variables

```bash
# Reddit API (create app at https://www.reddit.com/prefs/apps - use "script" type)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=RedditSentinel/0.1.0 (personal bot detection)

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Cache TTLs
SCORE_CACHE_TTL_HOURS=48

# Logging
LOG_LEVEL=INFO
```

## Getting Started

1. Create the GitHub repo: `gh repo create reddit-sentinel --private`
2. Clone and set up: `git clone ... && cd reddit-sentinel`
3. Copy env file: `cp .env.example .env` and fill in Reddit credentials
4. Start backend: `cd backend && docker-compose up`
5. Test API: `curl http://localhost:8000/v1/health`
6. Load extension in Chrome developer mode
7. Browse Reddit and check console logs

## Notes for Claude Code

- Start with the backend - get the API working before touching the extension
- Use the heuristic scorer first, don't worry about ML training initially
- The phonetic error detection is the novel/interesting part - focus there
- Keep it simple - this is personal use, not a product
- Redis is required for caching but no other database needed
- Test with known bot accounts from r/TheseFuckingAccounts
