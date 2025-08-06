# Email Todo Extractor

An automated system that monitors Outlook emails and Fireflies meeting transcripts to extract and save todo items.

## Project Overview

This tool automatically:
1. Monitors incoming Outlook emails
2. Filters out spam/newsletters
3. Sends emails to AI for analysis
4. Extracts action items assigned to the user
5. Saves todos to a text file
6. (Future) Integrates with Fireflies for meeting transcript analysis

## Current Status

- ✅ Microsoft Graph API authentication working
- ✅ Email monitoring implemented
- ✅ Basic spam filtering
- 🚧 AI analysis integration pending
- 🚧 Todo extraction logic pending
- 🚧 Fireflies integration pending

## Technical Stack

- **Language**: Python 3.x
- **Email API**: Microsoft Graph API
- **Authentication**: MSAL (Microsoft Authentication Library)
- **AI**: Claude API (planned)
- **Dependencies**: msal, requests, python-dotenv

## Project Structure

```
ToDoExtractor/
├── main/
│   ├── email_monitor.py    # Core email monitoring logic
│   └── requirements.txt    # Python dependencies
├── .env                    # Environment variables (API keys)
└── claude.md              # This file
```

## Environment Variables

Required in `.env`:
- `CLIENT_ID`: Azure app registration ID
- `CLIENT_SECRET`: Azure app secret value
- `TENANT_ID`: Azure tenant ID  
- `USER_EMAIL`: Email address to monitor

## Azure Setup

1. Register app in Azure Portal
2. Grant Mail.Read permissions
3. Get admin consent
4. Create client secret

## Next Steps

1. **Integrate Claude API**
   - Add function to send email content to Claude
   - Parse Claude's response for action items
   - Handle rate limiting

2. **Todo Extraction Logic**
   - Identify emails requiring action (not just CC'd)
   - Extract specific, actionable tasks
   - Format as checklist items

3. **File Management**
   - Append todos to todos.txt
   - Implement duplicate detection
   - Add timestamp and source tracking

4. **Fireflies Integration**
   - Connect to Fireflies API
   - Fetch recent meeting transcripts
   - Search for "Dylan" mentions and action items
   - Merge with email todos

5. **Enhancement Ideas**
   - Real-time notifications
   - Priority detection
   - Due date extraction
   - Integration with task management tools

## Key Functions

### `EmailMonitor` class
- `get_access_token()`: Authenticates with Microsoft
- `get_recent_emails()`: Fetches new emails
- `is_actionable_email()`: Filters spam
- `monitor_inbox()`: Main monitoring loop

### Planned Functions
- `analyze_with_claude()`: Send to AI for analysis
- `extract_todos()`: Parse AI response
- `save_to_file()`: Append to todos.txt
- `check_fireflies()`: Get meeting action items

## Testing Notes

- Script checks for new emails every 30 seconds
- Currently filters basic spam patterns
- Timezone-aware datetime handling implemented
- Error handling for API failures

## Known Issues

- None currently active

## References

- [Microsoft Graph API Docs](https://docs.microsoft.com/en-us/graph/api/resources/mail-api-overview)
- [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
- [Claude API](https://docs.anthropic.com)