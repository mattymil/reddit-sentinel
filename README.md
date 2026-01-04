# RedditSentinel

A personal Reddit bot detection and filtering system that uses ML to identify suspected bot accounts and filters them from your Reddit feed via a browser extension.

## Overview

RedditSentinel detects bot accounts on Reddit by analyzing:
- **Account metadata** - Age, karma patterns, verification status
- **Behavioral patterns** - Posting frequency, subreddit diversity, timing entropy
- **Linguistic signals** - Phonetic spelling errors, article misuse, overly formal constructions

The system consists of a Python backend API (FastAPI) and a Chrome browser extension that hides or flags suspected bot posts in real-time.

## The Problem

Bot farms and human-bot operations infiltrate Reddit for karma farming, SEO manipulation, and astroturfing. A telltale sign: phonetic spelling errors like "leek" instead of "leak" suggest non-native English speakers who learned the language aurally. These often appear on reposted content that previously had correct spelling.

## Architecture

```
Browser Extension          Backend API (FastAPI)
     │                            │
     │  POST /v1/analyze/batch    │
     ├───────────────────────────►│
     │                            ├──► Reddit API (PRAW)
     │                            ├──► Feature Extraction
     │                            ├──► ML Model / Heuristics
     │◄────────────────────────────┤
     │  { scores, classifications }│
     │                            │
     ▼                            ▼
  Hide/Flag Posts            Redis Cache (48h TTL)
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Reddit API credentials ([create app here](https://www.reddit.com/prefs/apps) - use "script" type)
- Chrome browser (for extension)

### Backend Setup

```bash
# Clone the repo
git clone https://github.com/mattymil/reddit-sentinel.git
cd reddit-sentinel

# Configure environment
cp .env.example .env
# Edit .env with your Reddit API credentials

# Start services
cd backend
docker-compose up
```

The API will be available at `http://localhost:8000`. Check health at `http://localhost:8000/v1/health`.

### Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked" and select the `extension/` directory
4. Browse Reddit - the extension will analyze post authors automatically

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/health` | GET | Health check |
| `/v1/score/{username}` | GET | Get bot score for a user |
| `/v1/analyze/batch` | POST | Analyze multiple usernames |
| `/v1/feedback` | POST | Report false positive/negative |
| `/v1/stats` | GET | System statistics |

### Example Response

```json
{
  "username": "SuspiciousUser123",
  "bot_probability": 0.87,
  "confidence": 0.92,
  "classification": "likely_bot",
  "contributing_factors": [
    {"factor": "phonetic_error_score", "contribution": 0.23},
    {"factor": "account_age_days", "contribution": 0.18},
    {"factor": "posting_hour_entropy", "contribution": 0.15}
  ]
}
```

## Configuration

### Environment Variables

```bash
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=RedditSentinel/0.1.0

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
SCORE_CACHE_TTL_HOURS=48
LOG_LEVEL=INFO
```

### Extension Settings

Access via the extension popup or options page:

| Setting | Default | Description |
|---------|---------|-------------|
| Hide Threshold | 0.85 | Score above which posts are hidden |
| Flag Threshold | 0.60 | Score above which posts are flagged |
| Hide Mode | collapse | How to hide posts: collapse, blur, or remove |
| API Endpoint | localhost:8000 | Backend API URL |

## Detection Features

### Account Signals
- Account age (new accounts more suspicious)
- Karma per day (abnormally high = suspicious)
- Trophy count (legitimate users accumulate over time)
- Email verification status

### Behavioral Signals
- Subreddit entropy (low diversity = focused bot)
- Posting hour entropy (low = automated posting)
- Burst posting patterns
- Weekend activity ratio

### Linguistic Signals
- **Phonetic errors**: "leek/leak", "peak/pique interest", "loose/lose"
- **Article errors**: "a apple", "an book"
- **Overly formal**: "kindly", "do the needful", "revert back"
- Vocabulary richness
- Emoji density patterns

## Development

### Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/
```

### Project Structure

```
reddit-sentinel/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes and schemas
│   │   ├── collectors/   # Reddit data collection (PRAW)
│   │   ├── features/     # Feature extraction modules
│   │   └── models/       # ML model and heuristic scorer
│   └── tests/
├── extension/
│   ├── src/              # Extension JavaScript
│   └── manifest.json     # Chrome Manifest V3
├── training/             # ML training scripts and data
└── infrastructure/       # AWS deployment configs
```

## Roadmap

- [x] Project setup and planning
- [ ] Phase 1: Backend MVP (FastAPI + heuristic scorer)
- [ ] Phase 2: Browser extension
- [ ] Phase 3: ML model training and refinement
- [ ] Phase 4: AWS deployment

See the [GitHub Project](https://github.com/users/mattymil/projects/17) for detailed task tracking.

## License

Private project - not for distribution.
