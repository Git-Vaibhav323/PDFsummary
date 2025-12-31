# 🚀 Complete Deployment Guide: Netlify + Render

Deploy your PDF Intelligence chatbot with **Netlify (Frontend)** and **Render (Backend)**.

---

## ✅ Pre-Deployment Checklist

All issues have been fixed:
- ✅ NumPy pinned to `<2.0.0` for ChromaDB compatibility
- ✅ Model caching configured (`.model_cache/` directory)
- ✅ Model pre-download during build (`download_models.py`)
- ✅ CORS configured for Netlify domains
- ✅ Path aliases fixed (`@/` imports work)
- ✅ `frontend/lib/` folder tracked in git
- ✅ Health check endpoint configured
- ✅ Python 3.11.9 specified

---

## 📋 Prerequisites

1. ✅ GitHub account with code pushed
2. ✅ [Render account](https://render.com/) (free tier)
3. ✅ [Netlify account](https://netlify.com/) (free tier)
4. ✅ OpenAI API key
5. ✅ Mistral API key (optional)

---

## 🔧 PART 1: Deploy Backend on Render (10 minutes)

### Step 1: Create Web Service

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Click **"Build and deploy from a Git repository"**
4. Click **"Connect account"** (if first time) or **"Configure account"**
5. Select your repository: **`PDFsummary`**
6. Click **"Connect"**

### Step 2: Configure Service

Fill in these settings:

| Setting | Value |
|---------|-------|
| **Name** | `pdfsummary-backend` (or your choice) |
| **Region** | Choose closest to you (e.g., Oregon USA) |
| **Branch** | `main` |
| **Root Directory** | (leave empty) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install --upgrade pip && pip install -r requirements.txt && python download_models.py` |
| **Start Command** | `python run.py` |
| **Instance Type** | **Free** |

**IMPORTANT**: The build command will:
1. Install all dependencies
2. Pre-download the embedding model (takes 3-5 minutes)
3. Cache the model for runtime use

### Step 3: Add Environment Variables

Click **"Advanced"** → Scroll to **"Environment Variables"** → Click **"Add Environment Variable"**

Add these **4 variables** one by one:

#### Variable 1:
- **Key**: `PYTHON_VERSION`
- **Value**: `3.11.9`

#### Variable 2:
- **Key**: `OPENAI_API_KEY`
- **Value**: `sk-xxxxx` (your actual OpenAI API key)

#### Variable 3:
- **Key**: `MISTRAL_API_KEY`
- **Value**: `xxxxx` (your actual Mistral API key - optional but recommended)

#### Variable 4:
- **Key**: `ALLOWED_ORIGINS`
- **Value**: `https://*.netlify.app`
  - This allows all Netlify domains (production + deploy previews)
  - Or use specific URL after frontend deploys: `https://your-app.netlify.app`

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait 8-12 minutes for:
   - Dependencies installation (3-5 min)
   - Model download (3-5 min)
   - Service startup (1-2 min)
3. **DO NOT CLOSE THE PAGE** - watch the logs!

### Step 5: Verify Backend

Once deployed, you'll see: **"Your service is live 🎉"**

1. Copy your backend URL (e.g., `https://pdfsummary-backend.onrender.com`)
2. **Save this URL** - you'll need it for frontend!
3. Visit: `https://your-backend.onrender.com/health`
4. Should show:
   ```json
   {"status": "healthy", "message": "RAG PDF Intelligence API is running"}
   ```

✅ **Backend is ready!**

---

## 🎨 PART 2: Deploy Frontend on Netlify (5 minutes)

### Step 1: Create New Site

1. Go to https://app.netlify.com/
2. Click **"Add new site"** → **"Import an existing project"**
3. Click **"Deploy with GitHub"**
4. Click **"Configure the Netlify app on GitHub"** (if first time)
5. Select your repository: **`PDFsummary`**
6. Click **"Install"** or **"Save"**

### Step 2: Configure Build Settings

On the site configuration page:

| Setting | Value |
|---------|-------|
| **Site name** | Choose a name (e.g., `pdf-chatbot-yourname`) |
| **Branch to deploy** | `main` |
| **Base directory** | `frontend` ⬅️ **CRITICAL!** |
| **Build command** | `npm run build` |
| **Publish directory** | `frontend/.next` |

### Step 3: Add Environment Variable

Before deploying, add the backend URL:

1. Click **"Add environment variables"** (or skip to "Deploy site" and add later)
2. Click **"New variable"**
3. **Key**: `NEXT_PUBLIC_API_URL`
4. **Value**: `https://your-backend.onrender.com` 
   - Use your actual Render backend URL from Part 1, Step 5
   - **NO trailing slash!**

### Step 4: Deploy

1. Click **"Deploy [site-name]"**
2. Wait 2-4 minutes for build
3. Watch the deploy log for any errors

### Step 5: Verify Frontend

Once deployed:

1. You'll get a URL like: `https://pdf-chatbot-yourname.netlify.app`
2. Click **"Open production deploy"** or visit your URL
3. You should see your chatbot interface! 🎉

---

## 🔗 PART 3: Connect Frontend & Backend (2 minutes)

### Update Backend CORS (If Needed)

If you used a specific Netlify URL instead of the wildcard:

1. Go back to **Render dashboard**
2. Go to your backend service
3. Click **"Environment"** in left sidebar
4. Find `ALLOWED_ORIGINS` variable
5. Update value to your Netlify URL: `https://your-site.netlify.app`
6. Service will auto-redeploy (1-2 minutes)

### Update Frontend API URL (If Needed)

If you didn't set it in Step 3:

1. Go to **Netlify dashboard**
2. Go to your site → **"Site configuration"** → **"Environment variables"**
3. Click **"Add a variable"**
4. **Key**: `NEXT_PUBLIC_API_URL`
5. **Value**: `https://your-backend.onrender.com` (your Render URL)
6. Click **"Redeploy"** in Deploys tab

---

## 🧪 PART 4: Test Your App

### 1. Test Backend Directly

```bash
curl https://your-backend.onrender.com/health
```

Expected response:
```json
{"status":"healthy","message":"RAG PDF Intelligence API is running"}
```

### 2. Test Frontend

1. Open your Netlify URL: `https://your-site.netlify.app`
2. You should see the chatbot interface
3. **Important**: First load might take 30-60 seconds (Render cold start)

### 3. Test PDF Upload

1. Click **"Upload PDF"** or drag a PDF file
2. Wait 15-30 seconds for processing
3. You should see: "✅ PDF uploaded successfully!"
4. Status should show: "Ready to answer questions"

### 4. Test Chat

1. Type a question about your PDF
2. Click send or press Enter
3. Wait 5-10 seconds
4. You should get an AI response! 🎉

### 5. Check Browser Console

Press `F12` → Console tab:
- ✅ Should see: "Backend is healthy and reachable"
- ✅ Should see: "✅ Backend connected successfully"
- ❌ Should NOT see CORS errors

---

## 📊 Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| **Backend cold start** | 30-60 seconds | First request after 15 min idle |
| **Backend warm** | 1-2 seconds | Subsequent requests |
| **PDF upload** | 15-30 seconds | Depends on PDF size |
| **Model loading** | 2-5 seconds | Uses cached model |
| **Chat response** | 5-10 seconds | AI processing time |
| **Frontend load** | 1-3 seconds | Very fast on Netlify |

---

## 🐛 Troubleshooting

### Backend Issues on Render

#### ❌ "Port scan timeout" / "Failed to bind to port"

**Cause**: Backend isn't starting properly or took too long to download model.

**Fix**:
1. Check Render logs (look for errors)
2. Make sure `download_models.py` completed during build
3. Model should download in **build phase**, not startup
4. Check logs for: "✅ Successfully downloaded and cached all-MiniLM-L6-v2"

#### ❌ "Error installing dependencies"

**Cause**: NumPy or other package compatibility issue.

**Fix**:
1. Check `requirements.txt` has `numpy>=1.24.0,<2.0.0`
2. Check `runtime.txt` has `python-3.11.9`
3. Redeploy: Render dashboard → Manual Deploy → Deploy latest commit

#### ❌ "Module not found" errors

**Cause**: Missing dependencies.

**Fix**:
1. Check all packages in `requirements.txt` are valid
2. Make sure build command includes: `pip install -r requirements.txt`

### Frontend Issues on Netlify

#### ❌ "Module not found: Can't resolve '@/lib/api'"

**Cause**: Path alias not resolving or `lib` folder not in git.

**Fix** (already done, but verify):
1. Check `frontend/tsconfig.json` has:
   ```json
   {
     "compilerOptions": {
       "baseUrl": ".",
       "paths": { "@/*": ["./*"] }
     }
   }
   ```
2. Check `frontend/lib/` folder exists in GitHub repo
3. Redeploy: Netlify → Deploys → Trigger deploy

#### ❌ "Page not found" (404 error)

**Cause**: Next.js app not building correctly.

**Fix** (already done):
1. Make sure `netlify.toml` has `@netlify/plugin-nextjs`
2. Build command is `npm run build`
3. Publish directory is `.next`

#### ❌ CORS Error: "No 'Access-Control-Allow-Origin' header"

**Cause**: Backend CORS not configured correctly.

**Fix**:
1. Check `ALLOWED_ORIGINS` in Render includes your Netlify URL
2. Use wildcard: `https://*.netlify.app`
3. Or specific URL: `https://your-site.netlify.app`
4. Redeploy backend after changing

#### ❌ "Backend not reachable" / "Network Error"

**Cause**: Wrong API URL or backend is down.

**Fix**:
1. Check `NEXT_PUBLIC_API_URL` in Netlify environment variables
2. Make sure URL is correct: `https://your-backend.onrender.com`
3. NO trailing slash!
4. Test backend directly: `curl https://your-backend.onrender.com/health`
5. If backend is down, wait for Render cold start (30-60 seconds)

---

## 🔄 Redeployment

### Update Your Code

```bash
git add .
git commit -m "Your changes"
git push origin main
```

**Both Netlify and Render** will auto-deploy! ✅

### Manual Redeploy

**Render**:
1. Go to service → **"Manual Deploy"**
2. Click **"Deploy latest commit"**

**Netlify**:
1. Go to site → **"Deploys"**
2. Click **"Trigger deploy"** → **"Deploy site"**

---

## 💰 Cost Estimate

| Service | Free Tier Limits | Cost |
|---------|------------------|------|
| **Render** | 750 hours/month, sleeps after 15 min idle | $0 |
| **Netlify** | 100 GB bandwidth, 300 build minutes/month | $0 |
| **Total** | Perfect for personal/demo projects | **$0/month** |

---

## 🎯 Important Notes

### Render Free Tier Limitations

1. **Sleep after 15 minutes idle**
   - First request after sleep takes 30-60 seconds
   - Subsequent requests are fast (1-2 seconds)
   - Solution: Use a ping service or upgrade to paid plan ($7/month)

2. **750 hours per month limit**
   - That's ~25 hours per day
   - More than enough for personal use
   - If exceeded, service stops until next month

3. **Build time limit: 15 minutes**
   - Our build takes 8-12 minutes (within limit)
   - Includes model download

### Netlify Free Tier Limitations

1. **100 GB bandwidth/month**
   - Plenty for most projects
   - Frontend is small (~5MB)

2. **300 build minutes/month**
   - Our builds take 2-4 minutes
   - ~75 deploys per month

---

## ✅ Final Checklist

- [ ] Backend deployed on Render
- [ ] Backend health check returns 200 OK
- [ ] Backend URL copied
- [ ] Frontend deployed on Netlify
- [ ] Frontend loads without errors
- [ ] `NEXT_PUBLIC_API_URL` set in Netlify
- [ ] `ALLOWED_ORIGINS` set in Render
- [ ] No CORS errors in browser console
- [ ] Can upload PDF successfully
- [ ] Can ask questions and get responses
- [ ] Both services auto-deploy on git push

---

## 🎉 You're Live!

Your PDF Intelligence chatbot is now deployed:

- 🌐 **Frontend**: `https://your-site.netlify.app`
- 🔌 **Backend**: `https://your-backend.onrender.com`
- 📖 **API Docs**: `https://your-backend.onrender.com/docs`

Share your frontend URL with anyone to let them use your chatbot!

---

## 🆘 Still Having Issues?

1. **Check Render logs**:
   - Dashboard → Your service → Logs tab
   - Look for red error messages

2. **Check Netlify logs**:
   - Dashboard → Your site → Deploys → Click latest deploy
   - Check "Deploy log" for build errors

3. **Check browser console**:
   - Press F12 → Console tab
   - Look for red errors
   - Check Network tab for failed requests

4. **Test backend directly**:
   ```bash
   # Health check
   curl https://your-backend.onrender.com/health
   
   # Check if backend is responding
   curl -I https://your-backend.onrender.com/
   ```

---

**Good luck! This should work smoothly now!** 🚀

