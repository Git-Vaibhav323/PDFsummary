# Troubleshooting Connection Issues

## Backend is Running but Frontend Can't Connect

If you see "Cannot connect to backend" errors, follow these steps:

### Step 1: Verify Backend is Running
1. Check the terminal where you ran `python run.py`
2. You should see: `API will be available at http://127.0.0.1:XXXX`
3. Note the port number (e.g., 8001)

### Step 2: Update .env.local
1. Open `frontend/.env.local` (create it if it doesn't exist)
2. Set the port to match your backend:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8001
   ```
   (Replace 8001 with your actual backend port)

### Step 3: Restart Frontend (IMPORTANT!)
**Next.js only loads environment variables at startup!**

1. **Stop the frontend server:**
   - Press `Ctrl+C` in the terminal where `npm run dev` is running
   - Wait for it to fully stop

2. **Restart the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Check the browser console (F12):**
   - You should see: `✅ [Frontend] Backend is healthy and reachable!`
   - If you see errors, check the console messages

### Step 4: Verify Connection
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for health check messages
4. If you see connection errors, check:
   - Backend terminal shows it's running
   - Port number matches in .env.local
   - Frontend was restarted after .env.local change

### Common Issues

**Issue: "Cannot connect to backend"**
- ✅ Backend is running (check terminal)
- ✅ .env.local has correct port
- ❌ Frontend not restarted → **RESTART FRONTEND**

**Issue: CORS errors**
- Backend CORS is configured for ports 3000, 3001, 3002
- Make sure your frontend is running on one of these ports
- Check browser console for CORS error messages

**Issue: Port mismatch**
- Backend says: `http://127.0.0.1:8001`
- .env.local says: `http://localhost:8001` ✅ (this is correct, localhost = 127.0.0.1)
- If backend is on 8002, update .env.local to 8002

### Quick Test
Open in browser: `http://localhost:8001/health`
- Should return: `{"status":"healthy",...}`
- If this works, backend is fine, issue is frontend config

