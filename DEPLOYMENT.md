# Deployment Guide

This guide will help you deploy the RAG Bot PDF application:
- **Frontend**: Deploy to Netlify
- **Backend**: Deploy to Render

## Prerequisites

1. GitHub account with your code pushed to a repository
2. Netlify account (free tier available)
3. Render account (free tier available)
4. OpenAI API key
5. (Optional) Mistral API key for OCR features

---

## Backend Deployment (Render)

### Step 1: Prepare Your Repository

1. Ensure all your code is committed and pushed to GitHub
2. Make sure `render.yaml` is in the root directory
3. Verify `requirements.txt` is up to date

### Step 2: Deploy on Render

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +"** → **"Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service**:
   - **Name**: `ragbotpdf-backend` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run.py`
   - **Plan**: Free (or paid if you need more resources)

5. **Set Environment Variables** in Render dashboard:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   MISTRAL_API_KEY=your_mistral_api_key_here (optional)
   ALLOWED_ORIGINS=https://your-app.netlify.app
   ```
   
   **Important**: 
   - Replace `your-app.netlify.app` with your actual Netlify URL (you'll get this after deploying frontend)
   - If you have multiple origins, separate them with commas: `https://app1.netlify.app,https://app2.netlify.app`

6. **Click "Create Web Service"**
7. Wait for deployment to complete (5-10 minutes for first deployment)
8. **Copy your Render backend URL** (e.g., `https://ragbotpdf-backend.onrender.com`)

### Step 3: Verify Backend

1. Visit `https://your-backend-url.onrender.com/health` - should return `{"status": "healthy"}`
2. Visit `https://your-backend-url.onrender.com/docs` - should show FastAPI docs

---

## Frontend Deployment (Netlify)

### Step 1: Prepare Frontend

1. Ensure `netlify.toml` is in the `frontend/` directory
2. Make sure all dependencies are in `package.json`

### Step 2: Deploy on Netlify

#### Option A: Deploy via Netlify Dashboard (Recommended)

1. **Go to Netlify Dashboard**: https://app.netlify.com
2. **Click "Add new site"** → **"Import an existing project"**
3. **Connect to Git provider** (GitHub/GitLab/Bitbucket)
4. **Select your repository**
5. **Configure build settings**:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `.next`
   - **Node version**: `20` (set in Build & deploy → Environment → Node version)

6. **Set Environment Variables**:
   - Go to **Site settings** → **Environment variables**
   - Add:
     ```
     NEXT_PUBLIC_API_URL=https://your-backend-url.onrender.com
     ```
     Replace `your-backend-url.onrender.com` with your actual Render backend URL

7. **Click "Deploy site"**
8. Wait for deployment (2-5 minutes)
9. **Copy your Netlify URL** (e.g., `https://your-app.netlify.app`)

#### Option B: Deploy via Netlify CLI

```bash
cd frontend
npm install -g netlify-cli
netlify login
netlify deploy --prod
```

Set environment variables via Netlify dashboard after deployment.

### Step 3: Update Backend CORS

1. Go back to **Render Dashboard**
2. Go to your backend service → **Environment**
3. Update `ALLOWED_ORIGINS` to include your Netlify URL:
   ```
   ALLOWED_ORIGINS=https://your-app.netlify.app
   ```
4. **Save** and wait for automatic redeployment

### Step 4: Verify Frontend

1. Visit your Netlify URL
2. Try uploading a PDF
3. Test the chat functionality

---

## Post-Deployment Checklist

- [ ] Backend is accessible at Render URL
- [ ] Backend `/health` endpoint returns healthy status
- [ ] Frontend is accessible at Netlify URL
- [ ] Frontend can connect to backend (check browser console)
- [ ] PDF upload works
- [ ] Chat functionality works
- [ ] CORS is configured correctly (no CORS errors in browser console)

---

## Troubleshooting

### Backend Issues

**Problem**: Backend fails to start
- **Solution**: Check Render logs for errors. Common issues:
  - Missing environment variables
  - Port binding issues (should be handled automatically)
  - Import errors

**Problem**: Backend returns 503 or timeout
- **Solution**: 
  - Free tier on Render spins down after 15 minutes of inactivity
  - First request after spin-down takes 30-60 seconds
  - Consider upgrading to paid plan for always-on service

**Problem**: CORS errors
- **Solution**: 
  - Verify `ALLOWED_ORIGINS` in Render includes your Netlify URL
  - Check that URL matches exactly (including `https://`)
  - Redeploy backend after changing environment variables

### Frontend Issues

**Problem**: Frontend can't connect to backend
- **Solution**: 
  - Verify `NEXT_PUBLIC_API_URL` in Netlify environment variables
  - Check that backend URL is correct (no trailing slash)
  - Ensure backend is running (check Render dashboard)

**Problem**: Build fails on Netlify
- **Solution**:
  - Check Node version (should be 20)
  - Verify all dependencies are in `package.json`
  - Check Netlify build logs for specific errors

**Problem**: Environment variables not working
- **Solution**:
  - Next.js requires `NEXT_PUBLIC_` prefix for client-side variables
  - Redeploy after adding/changing environment variables
  - Clear browser cache

### Database/Storage Issues

**Problem**: ChromaDB data is lost on redeploy
- **Solution**: 
  - Render free tier doesn't persist disk data between deploys
  - Consider using Render disk mounts (configured in `render.yaml`)
  - Or use external database service for production

---

## Environment Variables Reference

### Backend (Render)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key | `sk-...` |
| `MISTRAL_API_KEY` | No | Mistral API key for OCR | `...` |
| `ALLOWED_ORIGINS` | Yes | Comma-separated list of allowed origins | `https://app.netlify.app` |
| `PORT` | Auto | Port provided by Render | `10000` |

### Frontend (Netlify)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL | `https://backend.onrender.com` |

---

## Cost Considerations

### Render Free Tier
- 750 hours/month free
- Services spin down after 15 minutes of inactivity
- First request after spin-down has cold start delay
- Disk storage: 1GB free

### Netlify Free Tier
- 100GB bandwidth/month
- 300 build minutes/month
- Unlimited sites
- Automatic HTTPS

### Recommended for Production
- **Render**: Upgrade to Starter ($7/month) for always-on service
- **Netlify**: Free tier is usually sufficient for small-medium traffic

---

## Security Notes

1. **Never commit API keys** to Git
2. **Use environment variables** for all secrets
3. **Enable HTTPS** (automatic on both platforms)
4. **Set CORS origins** explicitly (don't use `*` in production)
5. **Regularly rotate API keys**

---

## Updating Your Deployment

### Backend Updates
1. Push changes to GitHub
2. Render automatically detects changes and redeploys
3. Monitor deployment logs

### Frontend Updates
1. Push changes to GitHub
2. Netlify automatically detects changes and redeploys
3. Monitor deployment logs

---

## Support

- **Render Docs**: https://render.com/docs
- **Netlify Docs**: https://docs.netlify.com
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Next.js Docs**: https://nextjs.org/docs

