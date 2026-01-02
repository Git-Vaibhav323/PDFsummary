# Chart Visualization Debugging Guide

## ✅ What I've Implemented

### Method 1: Recharts (Current Implementation)
- ✅ Replaced Chart.js with **Recharts** (simpler, more React-friendly)
- ✅ Created `SimpleChart.tsx` component
- ✅ Updated `ChatMessage.tsx` to use Recharts
- ✅ Added comprehensive logging

### Method 2: Backend Image Generation (Fallback)
- Backend already generates base64 images
- Can be used if frontend charts fail

## 🔍 How to Debug

### Step 1: Check Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for these logs:
   - `Full API Response:` - Shows what backend returned
   - `Mapped visualization:` - Shows processed visualization
   - `Chart data:` - Shows chart object
   - `Table data:` - Shows table data

### Step 2: Check Backend Logs
Look for these in your backend terminal:
- `Generated {type} chart successfully`
- `Chart data: type=bar, has_labels=True, has_values=True`
- `Returning visualization result:`

### Step 3: Check Network Tab
1. Open DevTools → Network tab
2. Find the `/chat` request
3. Click on it → Response tab
4. Check if `chart` field exists with `labels` and `values`

## 🐛 Common Issues & Fixes

### Issue 1: "No chart data in response"
**Symptom:** Console shows `chart: null` or `chart: undefined`

**Fix:**
- Check if backend visualization pipeline is running
- Verify PDF has numerical data
- Check backend logs for visualization errors

### Issue 2: "Chart data exists but not rendering"
**Symptom:** Console shows chart data but no chart appears

**Fix:**
- Check if `labels` and `values` arrays have same length
- Verify values are numbers (not strings)
- Check browser console for React errors

### Issue 3: "Module not found errors"
**Symptom:** Webpack errors about missing modules

**Fix:**
```bash
cd frontend
rm -rf .next node_modules/.cache
npm install
npm run dev
```

## 🧪 Test Cases

### Test 1: Simple Bar Chart
**Question:** "Show me revenue by year"

**Expected Response:**
```json
{
  "answer": "...",
  "chart": {
    "type": "bar",
    "title": "Revenue by Year",
    "labels": ["2021", "2022", "2023"],
    "values": [100000, 120000, 150000],
    "xAxis": "Year",
    "yAxis": "Revenue"
  }
}
```

### Test 2: Table
**Question:** "Show me the balance sheet"

**Expected Response:**
```json
{
  "answer": "...",
  "chart": {
    "type": "table",
    "headers": ["Item", "Amount"],
    "rows": [["Revenue", "100000"], ["Expenses", "50000"]],
    "title": "Balance Sheet"
  }
}
```

## 🔧 Quick Fixes

### Fix 1: Clear Cache and Rebuild
```bash
cd frontend
rm -rf .next
npm run dev
```

### Fix 2: Reinstall Dependencies
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Fix 3: Check Backend Response
Add this to `app/api/routes.py` in the `/chat` endpoint:
```python
logger.info(f"Response chart: {response.get('chart')}")
logger.info(f"Response table: {response.get('table')}")
```

## 📊 Alternative Methods (If Current Doesn't Work)

### Method A: Use Backend Images Only
- Backend generates base64 images
- Frontend just displays images
- Most reliable, no frontend chart library needed

### Method B: Use Simple HTML Canvas
- No dependencies
- Draw charts with Canvas API
- Full control

### Method C: Use SVG Charts
- No dependencies
- Scalable vector graphics
- Custom implementation

## 🎯 Next Steps

1. **Test the current implementation** with Recharts
2. **Check browser console** for any errors
3. **Check backend logs** for visualization generation
4. **If still not working**, we'll implement Method A (backend images)

## 📝 Current Status

✅ Recharts installed and configured
✅ SimpleChart component created
✅ ChatMessage updated to use SimpleChart
✅ Logging added for debugging
✅ Fallback logic added

**Ready to test!** Upload a PDF and ask for charts, then check the console logs.

