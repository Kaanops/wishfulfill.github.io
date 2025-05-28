# WishFulfill.de Deployment Guide

## Quick Start
1. Frontend: Deploy to Vercel
2. Backend: Deploy to Railway or Heroku
3. Connect domain: wishfulfill.de

## Frontend Deployment (Vercel)
1. Go to vercel.com
2. Sign up with GitHub
3. Import your frontend folder
4. Connect domain wishfulfill.de

## Backend Deployment (Railway)
1. Go to railway.app
2. Deploy backend folder
3. Add environment variables

## Environment Variables Needed:
- PAYPAL_CLIENT_ID: [your PayPal client ID]
- PAYPAL_CLIENT_SECRET: [your PayPal secret]
- PAYPAL_ENVIRONMENT: sandbox
- MONGO_URL: [MongoDB connection string]