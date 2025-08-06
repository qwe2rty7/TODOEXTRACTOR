# GitHub Sync Setup

This feature automatically syncs your todos.txt to your GitHub repository so you can monitor them from anywhere.

## Local Setup (Works without token)
The app will use your existing git credentials to push todos.

## Railway Setup (Requires GitHub token)

1. **Create a GitHub Personal Access Token:**
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Give it a name like "TodoExtractor Railway"
   - Select scopes:
     - `repo` (full control of private repositories)
   - Copy the token

2. **Add to Railway:**
   - In Railway dashboard, go to your service
   - Variables tab
   - Add: `GITHUB_TOKEN` = your-token-here

3. **Deploy:**
   - Railway will automatically redeploy
   - Todos will now sync to GitHub automatically

## Monitoring Your Todos

After setup, view your todos at:
- **todos.txt**: https://github.com/qwe2rty7/TODOEXTRACTOR/blob/main/todos.txt
- **Structured JSONs**: https://github.com/qwe2rty7/TODOEXTRACTOR/tree/main/structured_todos

The todos will auto-update whenever new action items are found in your emails or Fireflies transcripts.

## Troubleshooting

If sync fails:
1. Check Railway logs for error messages
2. Verify your GitHub token has `repo` scope
3. Ensure the repository is not protected with branch rules