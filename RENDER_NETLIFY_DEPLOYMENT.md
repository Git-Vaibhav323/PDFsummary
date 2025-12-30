# 🚀 Render + Netlify Deployment Guide

Complete guide to deploy your PDF Intelligence chatbot with **Render (Backend)** and **Netlify (Frontend)**.

---

## 📋 Prerequisites

1. ✅ GitHub account with your code pushed
2. ✅ [Render account](https://render.com/) (free tier)
3. ✅ [Netlify account](https://netlify.com/) (free tier)
4. ✅ OpenAI API key
5. ✅ Mistral API key (optional, for OCR)

---

## 🔧 Part 1: Deploy Backend on Render

### Step 1: Create New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select your repository: `PDFsummary`

### Step 2: Configure Service

**Basic Settings:**
- **Name**: `ragbotpdf-backend` (or your choice)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: Leave empty (root of repo)
- **Runtime**: Python 3
- **Build Command**: 
  ```bash
  pip install --upgrade pip && pip install -r requirements.txt && python download_models.py
  ```
- **Start Command**: 
  ```bash
  python run.py
  ```

**Instance Type:**
- Select **Free** tier

### Step 3: Set Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**:

| Key | Value | Notes |
|-----|-------|-------|
| `PYTHON_VERSION` | `3.11.9` | Python version |
| `OPENAI_API_KEY` | `sk-xxxxx` | Your OpenAI API key |
| `MISTRAL_API_KEY` | `xxxxx` | Your Mistral API key (optional) |
| `ALLOWED_ORIGINS` | `https://.*\.netlify\.app` | Allows all Netlify URLs (production + previews) |

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for build to complete
3. **Important**: Model download happens during build (not at startup!)
4. Once deployed, copy your backend URL (e.g., `https://ragbotpdf-backend.onrender.com`)

### ✅ Verify Backend

Visit: `https://your-backend.onrender.com/health`

You should see:
```json
{"status": "healthy", "message": "RAG PDF Intelligence API is running"}
```

---

## 🎨 Part 2: Deploy Frontend on Netlify

### Step 1: Create New Site

1. Go to [Netlify Dashboard](https://app.netlify.com/)
2. Click **"Add new site"** → **"Import an existing project"**
3. Choose **GitHub** and authorize
4. Select your repository: `PDFsummary`

### Step 2: Configure Build Settings

**Build Settings:**
- **Base directory**: `frontend`
- **Build command**: `npm run build`
- **Publish directory**: `frontend/.next`
- **Branch**: `main`

### Step 3: Set Environment Variables

Go to **"Site settings"** → **"Environment variables"** → **"Add a variable"**:

| Key | Value | Notes |
|-----|-------|-------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.onrender.com` | Your Render backend URL (NO trailing slash) |
| `NODE_VERSION` | `20` | Node.js version |

**⚠️ CRITICAL**: Use your actual Render backend URL from Part 1, Step 4!

### Step 4: Deploy

1. Click **"Deploy site"**
2. Wait 2-3 minutes for build
3. Once deployed, you'll get a URL like: `https://random-name-123.netlify.app`

### Step 5: Update CORS in Render

1. Go back to **Render Dashboard**
2. Go to your backend service → **"Environment"**
3. Update `ALLOWED_ORIGINS`:
   - **Option 1** (specific): `https://your-site-name.netlify.app`
   - **Option 2** (all Netlify): `https://.*\.netlify\.app` (already set!)
4. Save changes (service will auto-redeploy)

---

## 🧪 Testing Your Deployment

### 1. Test Backend Health
```bash
curl https://your-backend.onrender.com/health
```
Should return: `{"status": "healthy", ...}`

### 2. Test Frontend
1. Open your Netlify URL
2. Upload a PDF file
3. Ask questions about the PDF
4. Should work within 10-20 seconds!

### 3. Check Browser Console
Press F12 → Console tab:
- ✅ No CORS errors
- ✅ "Backend connected successfully" message
- ✅ API requests returning 200 status

---

## 🐛 Troubleshooting

### Backend Issues

**❌ Build fails: "ModuleNotFoundError"**
- **Fix**: Check `requirements.txt` has all dependencies
- **Fix**: Make sure Python version is 3.11.9

**❌ Service times out / doesn't start**
- **Fix**: Check logs in Render dashboard
- **Fix**: Ensure `download_models.py` completes during build (not runtime)
- **Fix**: Increase health check timeout in Render settings

**❌ "Port scan timeout"**
- **Fix**: Render sets `PORT` env var automatically - check `run.py` uses it
- **Fix**: Backend should bind to `0.0.0.0`, not `localhost`

**❌ NumPy compatibility error**
- **Fix**: Already handled - `requirements.txt` pins `numpy<2.0.0`

### Frontend Issues

**❌ "Module not found: Can't resolve '@/lib/api'"**
- **Fix**: Already fixed in `tsconfig.json`, `next.config.js`, and `jsconfig.json`
- **Fix**: Ensure `frontend/lib/` folder is committed to git (check `.gitignore`)

**❌ "Page not found" (404)**
- **Fix**: Already fixed - `netlify.toml` includes `@netlify/plugin-nextjs`

**❌ CORS error in browser
- **Fix**: Update `ALLOWED_ORIGINS` in Render to match your Netlify URL
- **Fix**: Use regex: `https://.*\.netlify\.app` to allow all Netlify URLs

**❌ "Backend not reachable" error
- **Fix**: Check `NEXT_PUBLIC_API_URL` is set correctly in Netlify
- **Fix**: NO trailing slash in URL
- **Fix**: Ensure Render backend is running and healthy

---

## 📊 Expected Performance

### Backend (Render Free Tier)
- ✅ **Cold start**: 30-60 seconds (when idle for 15+ min)
- ✅ **Warm start**: 1-2 seconds
- ✅ **PDF upload + processing**: 10-30 seconds
- ✅ **Chat response**: 3-8 seconds

### Frontend (Netlify)
- ✅ **Page load**: < 3 seconds
- ✅ **Build time**: 2-3 minutes
- ✅ **Deploy previews**: Automatic for PRs

---

## 🔄 Redeployment

### Update Code
```bash
git add .
git commit -m "Your changes"
git push origin main
```

**Netlify**: Auto-deploys on push ✅  
**Render**: Auto-deploys on push ✅

### Manual Redeploy
- **Netlify**: Deploys → Trigger deploy
- **Render**: Manual Deploy → Deploy latest commit

---

## 💰 Cost Estimate

| Service | Free Tier | Limits |
|---------|-----------|--------|
| **Render** | ✅ Yes | 750 hours/month, sleeps after 15 min idle |
| **Netlify** | ✅ Yes | 100 GB bandwidth, 300 build minutes |
| **Total** | **$0/month** | Perfect for personal/demo use |

---

## 🎯 Custom Domain (Optional)

### Netlify Frontend
1. Go to **Domain settings** → **Add custom domain**
2. Follow DNS setup instructions
3. Free HTTPS included!

### Render Backend
1. Go to **Settings** → **Custom Domain**
2. Add your domain
3. Update `NEXT_PUBLIC_API_URL` in Netlify with new domain

---

## 📝 Important Files

| File | Purpose | Location |
|------|---------|----------|
| `render.yaml` | Render configuration | Root |
| `frontend/netlify.toml` | Netlify configuration | Frontend folder |
| `requirements.txt` | Python dependencies | Root |
| `runtime.txt` | Python version for Render | Root |
| `download_models.py` | Pre-download embeddings | Root |

---

## ✅ Success Checklist

- [ ] Backend deployed on Render
- [ ] Backend health check returns 200
- [ ] Frontend deployed on Netlify
- [ ] No CORS errors in browser console
- [ ] Can upload PDF successfully
- [ ] Can ask questions and get responses
- [ ] Environment variables set correctly

---

## 🆘 Still Having Issues?

1. **Check Render logs**: Dashboard → Logs
2. **Check Netlify logs**: Deploys → Deploy details → Deploy log
3. **Check browser console**: F12 → Console tab
4. **Check network tab**: F12 → Network tab (look for failed requests)

---

## 🎉 You're Done!

Your PDF Intelligence chatbot is now live:
- 🔗 **Frontend**: `https://your-site.netlify.app`
- 🔗 **Backend**: `https://your-backend.onrender.com`

Share the frontend URL with anyone to let them use your chatbot!

