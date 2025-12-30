# 🚀 Vercel Deployment Guide (Frontend + Backend)

Complete guide to deploy **BOTH** your PDF Intelligence chatbot frontend and backend on **Vercel**.

---

## 🎯 Why Vercel for Both?

✅ **Single platform** - No CORS issues, everything in one place  
✅ **Free tier** - Generous limits for hobby projects  
✅ **Serverless backend** - Automatically scales, no cold starts like Render  
✅ **Git integration** - Auto-deploy on push  
✅ **Simple setup** - Much easier than Render/Railway  

---

## 📋 Prerequisites

1. ✅ [Vercel account](https://vercel.com/) (free tier)
2. ✅ GitHub account with your code pushed
3. ✅ OpenAI API key
4. ✅ Mistral API key (optional, for OCR)

---

## 🔧 Part 1: Deploy Backend on Vercel

### Step 1: Create Backend Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository: `PDFsummary`
4. **Important**: In project settings:
   - **Framework Preset**: Other
   - **Root Directory**: Leave empty (project root)
   - **Build Command**: Leave empty
   - **Output Directory**: Leave empty

### Step 2: Configure Environment Variables

Click **"Environment Variables"** and add:

| Variable Name | Value | Notes |
|---------------|-------|-------|
| `OPENAI_API_KEY` | `sk-xxxxx` | Your OpenAI API key |
| `MISTRAL_API_KEY` | `xxxxx` | Your Mistral API key (optional) |
| `PYTHON_VERSION` | `3.11` | Python version |
| `ALLOWED_ORIGINS` | `https://your-frontend.vercel.app` | Set after frontend deployment |

**Note**: You'll update `ALLOWED_ORIGINS` after deploying the frontend in Part 2.

### Step 3: Deploy Backend

1. Click **"Deploy"**
2. Wait 2-3 minutes for deployment
3. Once deployed, copy your backend URL:
   - Example: `https://pdfsummary-backend.vercel.app`
4. **Save this URL** - you'll need it for the frontend!

### ✅ Verify Backend

Visit: `https://your-backend.vercel.app/health`

You should see:
```json
{"status": "healthy", "message": "RAG PDF Intelligence API is running"}
```

---

## 🎨 Part 2: Deploy Frontend on Vercel

### Step 1: Create Frontend Project

1. Go back to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import the **same** GitHub repository: `PDFsummary`
4. **Important**: In project settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend` ⬅️ **CRITICAL!**
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

### Step 2: Configure Environment Variables

Click **"Environment Variables"** and add:

| Variable Name | Value | Notes |
|---------------|-------|-------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.vercel.app` | Your backend URL from Part 1 (NO trailing slash!) |
| `NODE_VERSION` | `20` | Node.js version |

**⚠️ CRITICAL**: Use your actual backend URL from Part 1, Step 3!

### Step 3: Deploy Frontend

1. Click **"Deploy"**
2. Wait 2-3 minutes for build
3. Once deployed, you'll get a URL like: `https://pdfsummary-frontend.vercel.app`

### Step 4: Update Backend CORS

Now that you have both URLs, update the backend:

1. Go to your **backend project** in Vercel
2. Go to **Settings** → **Environment Variables**
3. Update `ALLOWED_ORIGINS`:
   - Value: `https://your-frontend.vercel.app`
   - Or use wildcard: `https://*.vercel.app` (allows all Vercel domains)
4. **Redeploy** the backend:
   - Go to **Deployments** tab
   - Click the 3 dots on latest deployment → **Redeploy**

---

## 🧪 Testing Your Deployment

### 1. Test Backend
```bash
curl https://your-backend.vercel.app/health
```
Should return: `{"status": "healthy", ...}`

### 2. Test Frontend
1. Open your frontend URL: `https://your-frontend.vercel.app`
2. Upload a PDF file
3. Ask questions about the PDF
4. Everything should work! 🎉

### 3. Check Browser Console
Press F12 → Console tab:
- ✅ No CORS errors
- ✅ "Backend connected successfully" message
- ✅ API requests returning 200 status

---

## 📊 Expected Performance

| Operation | Time |
|-----------|------|
| Backend cold start | 1-3 seconds (Vercel serverless) |
| Backend warm | < 1 second |
| PDF upload + processing | 10-30 seconds |
| Chat response | 3-8 seconds |
| Frontend page load | < 2 seconds |

**Much faster than Render!** No 15-minute waits! 🚀

---

## 🐛 Troubleshooting

### Backend Issues

**❌ "Module not found" error**
- **Fix**: Make sure `api/index.py` exists in root
- **Fix**: Check `vercel.json` is in project root

**❌ "Function execution timed out"**
- **Fix**: The free tier has 10-second timeout for serverless functions
- **Fix**: For longer operations, consider Vercel Pro ($20/month) with 60-second timeout
- **Alternative**: Use Render for backend (longer timeouts) + Vercel for frontend

**❌ Model download fails**
- **Fix**: Vercel serverless functions have limited disk space
- **Fix**: Model will be downloaded on each cold start (not ideal)
- **Solution**: Consider using Render for backend (persistent storage) + Vercel for frontend

### Frontend Issues

**❌ "Module not found: Can't resolve '@/lib/api'"**
- **Fix**: Already fixed in `tsconfig.json` and `next.config.js`
- **Fix**: Make sure Root Directory is set to `frontend`

**❌ CORS error in browser**
- **Fix**: Update `ALLOWED_ORIGINS` in backend environment variables
- **Fix**: Include your frontend URL: `https://your-frontend.vercel.app`
- **Fix**: Or use wildcard: `https://*.vercel.app`

**❌ "Backend not reachable"**
- **Fix**: Check `NEXT_PUBLIC_API_URL` in frontend environment variables
- **Fix**: NO trailing slash in URL
- **Fix**: Make sure backend is deployed and healthy

---

## ⚠️ Important Vercel Limitations

### Backend Serverless Limitations:

1. **Function Timeout**:
   - Free tier: 10 seconds max
   - Pro tier: 60 seconds max
   - **Issue**: PDF processing might timeout on free tier for large PDFs

2. **Function Size**:
   - Max 50MB (uncompressed)
   - **Issue**: With ML models, might exceed limit

3. **Disk Space**:
   - Ephemeral filesystem (no persistence between requests)
   - **Issue**: Model cache doesn't persist (will re-download)

### 💡 Recommended Hybrid Approach

If you hit Vercel backend limitations:

**Option A: Hybrid Deployment (Recommended)**
- ✅ **Frontend on Vercel** (fast, reliable)
- ✅ **Backend on Render** (longer timeouts, persistent storage)
- This gives you the best of both worlds!

**Option B: Full Vercel with Pro**
- Upgrade to Vercel Pro ($20/month)
- Get 60-second timeouts and more resources

---

## 🔄 Redeployment

### Update Code
```bash
git add .
git commit -m "Your changes"
git push origin main
```

**Both frontend and backend** auto-redeploy on push! ✅

### Manual Redeploy
- Go to project → Deployments → Latest → Redeploy

---

## 💰 Cost Estimate

| Service | Free Tier | Limits |
|---------|-----------|--------|
| **Vercel (Frontend)** | ✅ Yes | 100 GB bandwidth, unlimited sites |
| **Vercel (Backend)** | ✅ Yes | 100 GB bandwidth, 100 GB-hours serverless |
| **Total** | **$0/month** | Great for personal use |

**Note**: For production use with many users, consider Vercel Pro or hybrid approach.

---

## 🎯 Custom Domain (Optional)

### Frontend
1. Go to Frontend Project → **Settings** → **Domains**
2. Add your custom domain
3. Follow DNS instructions
4. Free HTTPS included!

### Backend
1. Go to Backend Project → **Settings** → **Domains**
2. Add API subdomain (e.g., `api.yourdomain.com`)
3. Update `NEXT_PUBLIC_API_URL` in frontend to new domain

---

## ✅ Success Checklist

- [ ] Backend deployed on Vercel
- [ ] Backend `/health` endpoint returns 200
- [ ] Frontend deployed on Vercel
- [ ] Frontend loads without errors
- [ ] `NEXT_PUBLIC_API_URL` set correctly
- [ ] `ALLOWED_ORIGINS` includes frontend URL
- [ ] No CORS errors in browser console
- [ ] Can upload PDF successfully
- [ ] Can ask questions and get responses

---

## 🆘 Still Having Issues?

### Check Vercel Logs

**Backend logs**:
1. Go to backend project
2. Click **"Deployments"**
3. Click on latest deployment
4. Check **"Functions"** tab for errors

**Frontend logs**:
1. Go to frontend project
2. Click **"Deployments"**  
3. Click on latest deployment
4. Check build logs

### Check Browser

1. Press F12 → Console tab
2. Look for errors (red text)
3. Check Network tab for failed requests

---

## 🎉 You're Done!

Your PDF Intelligence chatbot is now live on Vercel:
- 🔗 **Frontend**: `https://your-frontend.vercel.app`
- 🔗 **Backend**: `https://your-backend.vercel.app`

Share the frontend URL with anyone!

---

## 📝 Alternative: Hybrid Deployment

If Vercel backend has issues (timeouts/model size), use this setup:

- ✅ **Frontend**: Vercel (fast, free, reliable)
- ✅ **Backend**: Render (longer timeouts, persistent storage, free)

This combines the best of both platforms! See `RENDER_NETLIFY_DEPLOYMENT.md` for Render setup.

