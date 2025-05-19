# 🧪 SmartRead Testing Guide

## Quick Start

### 1. **Automated Setup**
```bash
# Make the setup script executable and run it
chmod +x setup.sh
./setup.sh
```

### 2. **Configure Environment**
Edit `backend/.env` with your actual API keys:
```env
MISTRAL_API_KEY=your_actual_mistral_key
GROQ_API_KEY=your_actual_groq_key
CLOUDINARY_CLOUD_NAME=your_cloudinary_name
CLOUDINARY_API_KEY=your_cloudinary_key
CLOUDINARY_API_SECRET=your_cloudinary_secret
```

### 3. **Start Application**
```bash
# Start everything at once
./start-all.sh

# Or start individually
./start-backend.sh improved  # Use improved version
./start-frontend.sh
```

## 🔍 **Testing Different Versions**

### **Original vs Improved Backend**

**Original Backend:**
```bash
cd backend
source .venv/bin/activate
python main.py
```

**Improved Backend:**
```bash
cd backend
source .venv/bin/activate
python main_improved.py
```

### **Feature Comparison**

| Feature | Original | Improved |
|---------|----------|----------|
| Async Processing | ❌ | ✅ |
| Redis Caching | ❌ | ✅ |
| Rate Limiting | ❌ | ✅ |
| Enhanced Error Handling | ❌ | ✅ |
| Performance Monitoring | ❌ | ✅ |
| Retry Logic | ❌ | ✅ |

## 🧪 **Manual Testing Steps**

### **1. Health Check**
```bash
# Test basic health
curl http://localhost:8000/ping

# Test detailed health (improved version only)
curl http://localhost:8000/health
```

### **2. PDF Processing Test**
```bash
# Test with a sample PDF URL
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://arxiv.org/pdf/2301.07041.pdf",
    "page_number": 1
  }'
```

### **3. Frontend Testing**
1. Open http://localhost:3000
2. Enter a PDF URL (e.g., from arXiv)
3. Wait for processing
4. Check annotations and related resources
5. Test page navigation
6. Try downloading the annotated PDF

## 🚀 **Performance Testing**

### **Load Testing with curl**
```bash
# Test multiple requests
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/extract" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://arxiv.org/pdf/2301.07041.pdf", "page_number": 1}' &
done
wait
```

### **Cache Testing**
```bash
# First request (should be slow)
time curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://arxiv.org/pdf/2301.07041.pdf", "page_number": 1}'

# Second request (should be fast with caching)
time curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://arxiv.org/pdf/2301.07041.pdf", "page_number": 1}'
```

## 🐛 **Debugging**

### **Check Logs**
```bash
# Backend logs
tail -f backend/app.log

# Docker logs
docker-compose logs -f
```

### **Database Inspection**
```bash
# MongoDB
docker exec -it smartread-mongodb mongosh smartread

# Redis
docker exec -it smartread-redis redis-cli
```

### **Common Issues & Solutions**

**1. "Module not found" errors**
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Database connection errors**
```bash
# Check if databases are running
docker-compose ps

# Restart databases
docker-compose restart
```

**3. API key errors**
- Verify your API keys in `backend/.env`
- Check if keys have proper permissions
- Test keys individually with curl

**4. CORS errors**
- Check `ALLOWED_ORIGINS` in `.env`
- Verify frontend URL matches allowed origins

## 📊 **Monitoring & Metrics**

### **Built-in Monitoring (Improved Version)**
```bash
# Get application metrics
curl http://localhost:8000/health

# Check specific endpoints
curl http://localhost:8000/docs
```

### **Performance Metrics**
- Response times
- Error rates
- Cache hit rates
- Memory usage

## 🔧 **Configuration Testing**

### **Feature Flags**
Test different configurations by modifying `backend/.env`:

```env
# Test without caching
ENABLE_CACHING=false

# Test without rate limiting
ENABLE_RATE_LIMITING=false

# Test with original routes
USE_ASYNC_ROUTES=false
```

### **Environment Testing**
```bash
# Development mode
ENVIRONMENT=development ./start-backend.sh improved

# Production mode
ENVIRONMENT=production ./start-backend.sh improved
```

## 📝 **Test Checklist**

### **Backend Tests**
- [ ] Health check responds
- [ ] PDF extraction works
- [ ] Caching improves performance
- [ ] Rate limiting prevents abuse
- [ ] Error handling works gracefully
- [ ] Database connections stable

### **Frontend Tests**
- [ ] UI loads correctly
- [ ] PDF upload/URL input works
- [ ] Annotations display properly
- [ ] Related resources load
- [ ] Page navigation works
- [ ] Download functionality works
- [ ] Error messages are user-friendly

### **Integration Tests**
- [ ] Frontend ↔ Backend communication
- [ ] Database persistence
- [ ] Cloudinary uploads
- [ ] Search functionality
- [ ] End-to-end PDF processing

## 🚨 **Troubleshooting**

### **If Backend Won't Start**
1. Check Python version (3.8+)
2. Verify virtual environment activation
3. Install missing dependencies
4. Check environment variables
5. Verify database connections

### **If Frontend Won't Start**
1. Check Node.js version (18+)
2. Run `npm install` again
3. Clear npm cache: `npm cache clean --force`
4. Check for port conflicts

### **If Processing Fails**
1. Verify API keys are correct
2. Check PDF URL accessibility
3. Monitor backend logs
4. Test with different PDF

## 📈 **Performance Benchmarks**

### **Expected Improvements**
- **Response Time**: 60-80% faster with caching
- **Throughput**: 3-4x higher with async processing
- **Error Rate**: 50% reduction with retry logic
- **Memory Usage**: 30% more efficient

### **Benchmark Commands**
```bash
# Measure response time
time curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{"url": "YOUR_PDF_URL", "page_number": 1}'

# Test concurrent requests
ab -n 10 -c 2 -T 'application/json' \
  -p post_data.json \
  http://localhost:8000/api/extract
```

## 🎯 **Success Criteria**

Your setup is successful when:
1. ✅ All health checks pass
2. ✅ PDF processing completes without errors
3. ✅ Frontend displays annotations correctly
4. ✅ Caching improves subsequent requests
5. ✅ No memory leaks or crashes
6. ✅ Error handling works gracefully

## 📞 **Getting Help**

If you encounter issues:
1. Check this guide first
2. Review error logs
3. Verify environment configuration
4. Test with minimal setup
5. Check API key permissions

Remember: The improved version includes better error messages and logging to help with debugging!
