# Railway Deployment Guide (RECOMMENDED)

## Why Railway > Render

✅ **No cold starts** - Always fast
✅ **Better performance** - Faster network and CPU
✅ **Simpler than Render** - Just works
✅ **$5/month starter** - Affordable
✅ **Persistent storage** - No data loss
✅ **Auto-deploy from GitHub** - Like Render but faster

---

## Deploy Backend on Railway

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub
3. **$5 free credit** for new users

### Step 2: Deploy Backend

1. **Click "New Project"**
2. **Select "Deploy from GitHub repo"**
3. **Choose your repository**: `PDFsummary`
4. **Railway will auto-detect** Python and deploy

### Step 3: Set Environment Variables

In Railway dashboard → Variables tab:

```
OPENAI_API_KEY=your_openai_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here (optional)
PYTHON_VERSION=3.11.9
```

**Don't set ALLOWED_ORIGINS yet** - we'll add it after frontend is deployed.

### Step 4: Get Your Backend URL

After deployment (3-5 minutes), copy your URL:
```
https://your-app.up.railway.app
```

---

## Deploy Frontend on Vercel

### Step 1: Create Vercel Account
1. Go to https://vercel.com
2. Sign up with GitHub

### Step 2: Deploy Frontend

1. **Click "Add New..." → Project**
2. **Import your GitHub repository**
3. **Configure**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

4. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
   ```
   (Use your Railway URL from Step 4 above)

5. **Click "Deploy"**

### Step 3: Copy Your Frontend URL

After deployment:
```
https://your-app.vercel.app
```

---

## Final Step: Update CORS

1. Go back to **Railway dashboard**
2. Go to **Variables**
3. **Add**:
   ```
   ALLOWED_ORIGINS=https://your-app.vercel.app
   ```
4. **Redeploy** (Railway will auto-redeploy)

---

## Test Your App

1. **Backend health**: Visit `https://your-app.up.railway.app/health`
   - Should see: `{"status": "healthy"}`

2. **Backend docs**: Visit `https://your-app.up.railway.app/docs`
   - Should see FastAPI documentation

3. **Frontend**: Visit `https://your-app.vercel.app`
   - Upload a PDF
   - Should work in **10-20 seconds** (not 15 minutes!)

---

## Costs

### Railway (Backend)
- **Trial**: $5 free credit (enough for ~1 month of testing)
- **Hobby Plan**: $5/month (500 hours, plenty for one app)
- **Pro Plan**: $20/month (unlimited)

**Recommendation**: Start with trial, upgrade to Hobby ($5/month) when needed

### Vercel (Frontend)
- **Hobby (Free)**: Perfect for this app
  - 100GB bandwidth
  - Unlimited deployments
  - Custom domains

**Total Cost**: **FREE for testing**, then **$5/month** for production

---

## Advantages Over Render + Netlify

| Feature | Railway + Vercel | Render + Netlify |
|---------|------------------|------------------|
| **Backend Cold Starts** | ❌ None | ✅ 30-60s |
| **Backend Speed** | ✅ Fast | ⚠️ Slow network |
| **Setup Complexity** | ✅ Simple | ⚠️ Medium |
| **Cost (Hobby)** | $5/month | Free (with issues) |
| **PDF Upload Time** | ✅ 10-20s | ❌ 15+ minutes |
| **Reliability** | ✅ Excellent | ⚠️ Timeouts |

---

## Troubleshooting

### Backend won't start on Railway
- Check logs in Railway dashboard
- Verify `OPENAI_API_KEY` is set
- Make sure `runtime.txt` has `python-3.11.0`

### Frontend can't connect to backend
- Verify `NEXT_PUBLIC_API_URL` in Vercel
- Check CORS: `ALLOWED_ORIGINS` in Railway
- Redeploy both if needed

### Upload still slow
- Check Railway logs for errors
- Model should download during build (not runtime)
- Contact me if issues persist

---

## Migration from Render

If you already have data on Render:
1. Deploy to Railway (fresh start)
2. Test everything works
3. Delete Render service when satisfied

---

**Railway is THE solution for your use case.** It's what Render should have been.

