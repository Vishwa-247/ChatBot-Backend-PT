# Render Deployment Guide

## Prerequisites

1. **MongoDB Atlas Account** ✅ (Already configured)
2. **Render Account** (for hosting)
3. **API Keys** (Gemini, Groq - to be set in Render dashboard)

## Current Configuration

### ✅ Already Configured:
- **MongoDB URI**: `mongodb+srv://vishwa:chatbootpt@chatbotpt.98g3vwh.mongodb.net/`
- **Cloudinary**: 
  - Cloud Name: `daoymzszl`
  - API Key: `887668153728379`
  - API Secret: `C499vZns44C0lJ-tEWr4flp8vr8`

### 🔧 Still Need to Set in Render Dashboard:
- `GEMINI_API_KEY` (your Gemini API key)
- `GROQ_API_KEY` (your Groq API key)

## Step 1: Deploy to Render

### Option A: Using GitHub (Recommended)

1. **Push your code to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Ready for Render deployment with MongoDB and Cloudinary"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

3. **Configure the service**
   - **Name**: `ai-chatbot-backend`
   - **Root Directory**: `backend` (important!)
   - **Runtime**: Python 3.12
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Environment Variables** (Set these in Render dashboard):
   ```
   MONGO_URI=mongodb+srv://vishwa:chatbootpt@chatbotpt.98g3vwh.mongodb.net/
   CLOUDINARY_CLOUD_NAME=daoymzszl
   CLOUDINARY_API_KEY=887668153728379
   CLOUDINARY_API_SECRET=C499vZns44C0lJ-tEWr4flp8vr8
   GEMINI_API_KEY=your_gemini_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build and deployment

### Option B: Using render.yaml (Auto-deploy)

If you have the `render.yaml` file in your repository:
1. Render will automatically detect and use the configuration
2. You only need to set `GEMINI_API_KEY` and `GROQ_API_KEY` in the dashboard
3. All other variables are pre-configured

## Step 2: Test Your Deployment

1. **Health Check**: Visit `https://your-app.onrender.com/api/health`
2. **API Docs**: Visit `https://your-app.onrender.com/docs`
3. **Test Chat**: Use your frontend or test via API

## Step 3: Update Frontend (if needed)

If your frontend is configured to use localhost:8000, update it to use your Render URL:
- Change API base URL from `http://localhost:8000` to `https://your-app.onrender.com`

## Troubleshooting

### Common Issues:
1. **Build fails**: Check if all dependencies are in `requirements.txt`
2. **Import errors**: Make sure you're in the `backend` directory
3. **Environment variables**: Verify all are set in Render dashboard
4. **MongoDB connection**: Test the connection string locally first

### Logs:
- Check Render logs for any errors
- MongoDB connection issues will appear in the logs

## Success Indicators

✅ **Deployment successful** when you see:
- Build completes without errors
- Health check returns `{"status":"ok","message":"AI Chat API is running"}`
- API docs are accessible
- File uploads work (check Cloudinary dashboard)
- Chat functionality works

## Next Steps

After successful deployment:
1. Test all features (chat, file upload, web search)
2. Monitor logs for any issues
3. Set up custom domain (optional)
4. Configure auto-scaling (optional)
