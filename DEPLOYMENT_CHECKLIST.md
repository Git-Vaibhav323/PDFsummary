# Quick Deployment Checklist

## Before You Start
- [ ] Code is pushed to GitHub
- [ ] You have OpenAI API key
- [ ] You have Netlify account
- [ ] You have Render account

## Backend Deployment (Render)

### Step 1: Create Render Service
- [ ] Go to https://dashboard.render.com
- [ ] Click "New +" → "Web Service"
- [ ] Connect GitHub repository
- [ ] Select repository
- [ ] Configure:
  - Name: `ragbotpdf-backend`
  - Environment: `Python 3`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `python run.py`

### Step 2: Set Environment Variables
- [ ] `OPENAI_API_KEY` = your OpenAI API key
- [ ] `MISTRAL_API_KEY` = your Mistral API key (optional)
- [ ] `ALLOWED_ORIGINS` = (leave empty for now, update after frontend deploy)

### Step 3: Deploy
- [ ] Click "Create Web Service"
- [ ] Wait for deployment (5-10 minutes)
- [ ] Copy backend URL: `https://your-backend.onrender.com`
- [ ] Test: Visit `https://your-backend.onrender.com/health`

## Frontend Deployment (Netlify)

### Step 1: Create Netlify Site
- [ ] Go to https://app.netlify.com
- [ ] Click "Add new site" → "Import an existing project"
- [ ] Connect GitHub repository
- [ ] Select repository
- [ ] Configure:
  - Base directory: `frontend`
  - Build command: `npm run build`
  - Publish directory: `.next`

### Step 2: Set Environment Variables
- [ ] Go to Site settings → Environment variables
- [ ] Add: `NEXT_PUBLIC_API_URL` = `https://your-backend.onrender.com`
  (Use the backend URL from Render)

### Step 3: Deploy
- [ ] Click "Deploy site"
- [ ] Wait for deployment (2-5 minutes)
- [ ] Copy frontend URL: `https://your-app.netlify.app`

## Final Configuration

### Update Backend CORS
- [ ] Go back to Render dashboard
- [ ] Open your backend service → Environment
- [ ] Update `ALLOWED_ORIGINS` = `https://your-app.netlify.app`
- [ ] Save (auto-redeploys)

## Verification

- [ ] Backend health check: `https://your-backend.onrender.com/health`
- [ ] Frontend loads: `https://your-app.netlify.app`
- [ ] Upload PDF works
- [ ] Chat works
- [ ] No CORS errors in browser console

## Troubleshooting

**Backend won't start?**
- Check Render logs
- Verify environment variables are set
- Check `requirements.txt` is correct

**Frontend can't connect?**
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check backend is running
- Ensure CORS is configured

**CORS errors?**
- Verify `ALLOWED_ORIGINS` includes your Netlify URL
- Check URL matches exactly (https://)
- Redeploy backend after changing env vars

---

**Need help?** See `DEPLOYMENT.md` for detailed instructions.

