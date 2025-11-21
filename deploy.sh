#!/bin/bash
# Railway Deployment Script
# This script helps prepare your project for Railway deployment

echo "🚀 Preparing Sasai Wallet MCP Service for Railway Deployment"
echo "=" * 60

# Check if we're in the right directory
if [ ! -f "streamable_http_server.py" ]; then
    echo "❌ Error: streamable_http_server.py not found"
    echo "Please run this script from the mcp-service directory"
    exit 1
fi

# Validate required files
echo "📋 Checking deployment files..."
required_files=("Dockerfile" "requirements.txt" "src/core/server.py")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file found"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "🔧 Pre-deployment checklist:"
echo "1. ✅ Dockerfile created"
echo "2. ✅ requirements.txt updated"
echo "3. ✅ .dockerignore configured"
echo "4. ✅ railway.json configured"
echo "5. ⚠️  Environment variables need to be set in Railway dashboard"
echo ""
echo "📋 Next steps:"
echo "1. Push your code to GitHub"
echo "2. Connect your GitHub repo to Railway"
echo "3. Set environment variables in Railway dashboard"
echo "4. Deploy!"
echo ""
echo "🌐 After deployment, your MCP service will be available at:"
echo "https://your-app-name.up.railway.app/mcp"
