# Email Todo Extractor

Automatically monitors Outlook emails and Fireflies meeting transcripts to extract and save todo items using AI.

## Features

- Monitors Outlook emails in real-time
- Uses Claude AI to extract actionable todos
- Filters out spam and non-actionable emails
- Saves todos to local file and JSON format
- Integrates with Fireflies for meeting transcripts
- Multiple deployment options

## Quick Start

### Prerequisites

1. Azure App Registration with Mail.Read permissions
2. Anthropic API key for Claude
3. Python 3.11+

### Local Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and add your credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`

## Deployment Options

### Railway (Recommended - Easiest)

1. Push to GitHub
2. Connect repo to Railway
3. Add environment variables
4. Deploy automatically

[See detailed Railway guide](DEPLOY_RAILWAY.md)

### 🐳 Docker

```bash
docker-compose up -d
```

### 💻 Windows Task Scheduler

Run as Administrator:
```powershell
.\setup_windows_task.ps1
```

### ☁️ Cloud Platforms

- **Render**: Similar to Railway, connect GitHub and deploy
- **Heroku**: Uses Procfile, standard deployment
- **AWS/GCP**: Use Docker image or serverless functions

## Environment Variables

```env
CLIENT_ID=your_azure_app_client_id
CLIENT_SECRET=your_azure_app_client_secret
TENANT_ID=your_azure_tenant_id
USER_EMAIL=your_email@example.com
ANTHROPIC_API_KEY=your_anthropic_api_key
FIREFLIES_API_KEY=your_fireflies_api_key  # Optional
```

## How It Works

1. Checks inbox every 30 seconds
2. Filters spam and newsletters
3. Sends actionable emails to Claude AI
4. Extracts todos assigned to you
5. Saves to `todos.txt` and JSON format
6. Optionally checks Fireflies transcripts

## Project Structure

```
ToDoExtractor/
├── main.py                 # Entry point
├── Main/                   # Core application code
│   ├── email_monitor.py    # Email monitoring logic
│   ├── fireflies_monitor.py # Fireflies integration
│   └── todo_manager.py     # Todo file management
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── railway.json           # Railway deployment config
└── .env                   # Environment variables (create from .env.example)
```

## Monitoring

- Logs are saved to `email_monitor.log`
- Todos saved to `todos.txt`
- Structured data in `structured_todos/` folder

## Cost Considerations

- **Railway**: Free tier ~20 days/month, $5/month for 24/7
- **Claude API**: ~$0.01-0.02 per email analyzed
- **Microsoft Graph**: Free with limits
- **Fireflies**: Depends on your plan

## Troubleshooting

- **No emails detected**: Check timezone settings and API permissions
- **Claude errors**: Verify API key and rate limits
- **Railway deployment fails**: Ensure all files are in root directory

## License

MIT
