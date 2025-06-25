# Backend Repository Setup Guide

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and click "New repository"
2. Repository name: `ai-chatbot-backend`
3. Description: `FastAPI backend for AI chatbot with MongoDB and Cloudinary`
4. Make it Public or Private (your choice)
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

## Step 2: Connect and Push Backend Code

After creating the repository, run these commands in your backend directory:

```bash
# Add the new remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/ai-chatbot-backend.git

# Add all files
git add .

# Commit
git commit -m "Initial backend commit with MongoDB and Cloudinary integration"

# Push to main branch
git push -u origin main
```

## Step 3: Deploy to Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub account
4. Select the `ai-chatbot-backend` repository
5. Configure:
   - **Name**: `ai-chatbot-backend`
   - **Root Directory**: Leave empty (since we're in the backend folder)
   - **Runtime**: Python 3.12
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

6. **Environment Variables** (set these in Render dashboard):
   ```
   MONGO_URI=mongodb+srv://vishwa:chatbootpt@chatbotpt.98g3vwh.mongodb.net/
   CLOUDINARY_CLOUD_NAME=daoymzszl
   CLOUDINARY_API_KEY=887668153728379
   CLOUDINARY_API_SECRET=C499vZns44C0lJ-tEWr4flp8vr8
   GEMINI_API_KEY=your_gemini_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

7. Click "Create Web Service"

## Step 4: Test Backend Deployment

1. Wait for deployment to complete
2. Test health check: `https://your-backend.onrender.com/api/health`
3. Check API docs: `https://your-backend.onrender.com/docs`

## Step 5: Get Backend URL

Note down your backend URL (e.g., `https://ai-chatbot-backend.onrender.com`) - you'll need this for the frontend configuration.

---

## ✅ Backend Deployment Checklist

- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] Render service created
- [ ] Environment variables set
- [ ] Deployment successful
- [ ] Health check working
- [ ] API docs accessible
- [ ] Backend URL noted for frontend 
