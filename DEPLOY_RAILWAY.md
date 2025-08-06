# Railway Deployment Guide

## Quick Deploy Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Railway deployment files"
   git push
   ```

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `ToDoExtractor` repository
   - Railway will auto-detect the Python app

3. **Add Environment Variables**
   In Railway dashboard, go to Variables tab and add:
   ```
   CLIENT_ID=<your_azure_client_id>
   CLIENT_SECRET=<your_azure_client_secret>
   TENANT_ID=<your_azure_tenant_id>
   USER_EMAIL=<your_email>
   ANTHROPIC_API_KEY=<your_claude_api_key>
   FIREFLIES_API_KEY=<optional_fireflies_key>
   ```

4. **Deploy**
   - Railway will automatically deploy
   - Check logs in the "Deployments" tab
   - The app will run continuously as a background worker

## What I Fixed

- Added `main.py` in root directory (Railway needs this)
- Added `requirements.txt` in root (not in Main/ folder)
- Added `railway.json` for Railway configuration
- Added `Procfile` as backup for deployment
- Created proper Python path imports

## Monitoring

- View logs in Railway dashboard
- Check "Deployments" tab for status
- Monitor usage in "Metrics" tab

## Cost

- Railway free tier: 500 hours/month (~20 days continuous)
- Upgrade to Hobby plan ($5/month) for 24/7 operation

## Troubleshooting

If deployment fails:
1. Check logs in Railway dashboard
2. Verify all environment variables are set
3. Ensure GitHub repo is up to date
4. Check Python version compatibility (3.11+)