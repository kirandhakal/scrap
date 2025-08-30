# Web Scraper Application

![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Enabled-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)

An automated web scraping application that monitors multiple websites for specific content, extracts relevant documents, and sends real-time notifications via Telegram Bots.

## Features

- **Automated Scheduling**: Runs 3 times daily via GitHub Actions
- **Smart Content Detection**: Filters content based on customizable keywords
- **Multi-format Support**: Handles PDFs, images, and various document types  
- **Multi-site Monitoring**: Configurable URL lists for different categories
- **Telegram**: send msg to telegram
- **Docker Ready**: Containerized deployment
- **Multilingual**: Supports English and Nepali content detection

## Project Structure

```
scrap/
├── .github/
│   └── workflows/
│         ├── docker.yml             # docker conatinerlization
│         ├── scraper.yml           # GitHub Actions workflow
├── scraper.py                     #Main code 
├── logs/                         # if you want to check logs
├── Dockerfile                    # Docker configuration
├── requirements.txt              # Python dependencies
├── venv/                         #virtual enviroments    
└── README.md
```

## Quick Start

### 1. Setup Repository

```bash
git clone https://github.com/kirandhakal/scrap.git
cd scrap
```

### 2. Configure GitHub Secrets

Go to your repository **Settings** → **Secrets and variables** → **Actions** and add:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | `1234567890:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | Target chat/channel ID | `-1001234567890` |

### 3. Configure URLs

Edit `config/urls.py`:

```python
TARGET_URLS = {
    "government": [
        "https://example.gov.np/notices",
        "https://ministry.gov.np/announcements"
    ],
    "education": [
        "https://university.edu.np/results",
        "https://exam.board.np/notices"
    ],
    "jobs": [
        "https://jobportal.com/vacancies"
    ]
}
```

### 4. Configure Keywords

Edit `config/keywords.py`:

```python
# Add your keywords for content detection
NOTICE_KEYWORDS = [
    # Add notice-related keywords (English/Nepali)
    # Example: "notice", "सूचना", "announcement", "vacancy", "रिक्त", "result", "नतिजा"
]

FILE_EXTENSIONS = [
    # Add supported file types
    # Example: ".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"
]
```

## Automated Scheduling

The scraper runs automatically via GitHub Actions:(you can add cron time as you want from https://crontab.guru/)

```yaml
# .github/workflows/scraper.yml
schedule:
  - cron: '15 4 * * *'   # 10:00 AM NPT
  - cron: '15 7 * * *'   # 1:00  PM NPT  
  - cron: '15 11 * * *'  # 5:00  PM NPT
workflow_dispatch: {}    # Manual trigger option
```

### Manual Run
1. Go to **Actions** tab in your repository
2. Select **Web Scraper Automation**
3. Click **Run workflow**

## Telegram Setup

### Create Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command  
3. Get your bot token

### Get Chat ID
1. Add bot to your chat/channel
2. Send a test message
3. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Copy the chat ID from response

## Docker Deployment

### Quick Run
```bash
docker build -t web-scraper .
docker run web-scraper
```

### Docker Compose
```bash
docker-compose up -d
```

## Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally (configure secrets in environment)
python src/main.py
```

## VS Code Setup

Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

## Message Format

```
🔍 search website daily in give cron time (here 3 times)

📍 Source: Website
📄 Type: PDF , image etc
🎯 Keywords: search key words
⚡ Priority: High
🕐 Time: 2025-08-30 10:15 AM

📝 Title: Important Notice Regarding...

🔗 Link: [View Document](https://...)

📊 Summary: 15 URLs processed • 3 new items
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No notifications | Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` |
| Workflow not running | Verify GitHub Actions are enabled |
| No content found | Review keyword configuration |
| Rate limiting | Increase delays in scraper settings |

### View Logs
- **GitHub Actions**: Actions tab → Workflow run → Logs
- **Docker**: `docker-compose logs web-scraper`
- **Local**: Check `logs/scraper.log`

## Contributing if you want 

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Submit pull request



**⭐ Star this repository if you find it helpful! And Give some suggestion if you have **
