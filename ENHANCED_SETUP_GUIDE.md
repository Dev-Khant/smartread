# 🚀 SmartRead Enhanced Setup Guide

## Overview

SmartRead Enhanced integrates **Gemini 2.0 Flash** and **Tavily Search** for superior document processing and search capabilities.

## 🎯 Key Enhancements

### **Gemini 2.0 Flash Integration**
- **2M token context window** - Process entire documents at once
- **Google's caching system** - Intelligent caching for large documents
- **Advanced reasoning** - Better understanding and analysis
- **Multimodal capabilities** - Handle text, images, and PDFs natively

### **Tavily Search Integration**
- **Free API** - No cost for basic usage
- **AI-powered search** - Get AI-generated summaries
- **Academic search** - Specialized academic content discovery
- **Video search** - Find relevant educational videos
- **Enhanced relevance** - Better matching than traditional search

## 🔧 Setup Instructions

### **1. Get API Keys**

#### **Gemini API Key (Required for Enhanced Mode)**
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key
5. Copy the key

#### **Tavily API Key (Required for Enhanced Search)**
1. Go to [Tavily](https://tavily.com/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier includes 1,000 searches/month

#### **Optional API Keys**
- **Mistral**: For fallback OCR processing
- **Groq**: For fallback text processing
- **Cloudinary**: For file storage (or use local storage)

### **2. Installation**

```bash
# Clone the repository
git clone <repository-url>
cd smartread

# Install enhanced dependencies
cd backend
pip install -r requirements.txt

# Setup environment
cp .env.example .env
```

### **3. Configuration**

Edit `backend/.env`:

```env
# Processing Mode
PROCESSING_MODE=enhanced  # Use Gemini + Tavily

# Required for Enhanced Mode
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Optional (for fallback)
MISTRAL_API_KEY=your_mistral_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Database
MONGODB_URL=mongodb://localhost:27017/smartread
REDIS_URL=redis://localhost:6379

# Optional: Cloudinary (or use local storage)
CLOUDINARY_CLOUD_NAME=your_cloudinary_name
CLOUDINARY_API_KEY=your_cloudinary_key
CLOUDINARY_API_SECRET=your_cloudinary_secret
```

### **4. Start Services**

```bash
# Start databases
docker-compose up -d

# Start enhanced backend
python main_enhanced.py

# Start frontend (in another terminal)
cd ../web
npm install
npm run dev
```

## 🎛️ Processing Modes

SmartRead Enhanced supports multiple processing modes:

### **Enhanced Mode (Recommended)**
```env
PROCESSING_MODE=enhanced
```
- Uses Gemini 2.0 Flash for document processing
- Uses Tavily for search and related content
- Best performance for large documents
- AI-generated summaries and key topics

### **Auto Mode (Default)**
```env
PROCESSING_MODE=auto
```
- Automatically selects best available processor
- Falls back gracefully if API keys are missing
- Recommended for most users

### **Async Mode**
```env
PROCESSING_MODE=async
```
- Uses Mistral + Groq with async processing
- Enhanced error handling and retry logic
- Good for high-throughput scenarios

### **Original Mode**
```env
PROCESSING_MODE=original
```
- Uses original Mistral + Groq implementation
- Synchronous processing
- Minimal dependencies

## 🧪 Testing

### **Quick Test**
```bash
# Test enhanced features
python test_enhanced_features.py

# Check application info
curl http://localhost:8000/info

# Check enhanced health
curl http://localhost:8000/health/enhanced
```

### **Feature Testing**

**Test Gemini Processing:**
```bash
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://arxiv.org/pdf/2301.07041.pdf", "page_number": 1}'
```

**Test Tavily Search:**
```bash
curl "http://localhost:8000/api/search?query=machine%20learning&search_type=all"
```

## 📊 Performance Comparison

| Feature | Original | Enhanced (Gemini + Tavily) |
|---------|----------|---------------------------|
| Document Processing | Page-by-page | Entire document at once |
| Context Window | Limited | 2M tokens |
| Search Quality | Basic | AI-powered with summaries |
| Caching | Basic | Google's intelligent caching |
| Processing Speed | Moderate | Fast (with caching) |
| Understanding | Good | Excellent |
| Related Content | Limited | Comprehensive |

## 🔍 Enhanced Features

### **Document Processing**
- **Full document analysis** in one pass
- **AI-generated summaries** of the entire document
- **Key topics extraction** automatically
- **Better highlight detection** with context understanding
- **Intelligent caching** for large documents

### **Search & Discovery**
- **AI-powered search** with Tavily
- **Academic content discovery** from scholarly sources
- **Video tutorials** automatically found
- **AI-generated summaries** for search results
- **Related topics** suggestions

### **Performance Optimizations**
- **Google's caching system** for Gemini
- **Intelligent fallbacks** between processors
- **Async processing** for better throughput
- **Enhanced error handling** with retries

## 🚨 Troubleshooting

### **Common Issues**

**"Gemini API key not configured"**
- Ensure `GEMINI_API_KEY` is set in `.env`
- Verify the API key is valid
- Check Google AI Studio for quota limits

**"Tavily search failed"**
- Ensure `TAVILY_API_KEY` is set in `.env`
- Check Tavily dashboard for usage limits
- Verify internet connectivity

**"Processing timeout"**
- Large documents may take time on first processing
- Subsequent requests will be much faster due to caching
- Consider increasing timeout in client

**"No processors available"**
- Ensure at least one set of API keys is configured
- Check `/config` endpoint to see available features
- Use `PROCESSING_MODE=auto` for automatic fallback

### **Performance Optimization**

**For Large Documents:**
```env
GEMINI_MODEL=flash  # Fastest model
GEMINI_CACHE_TTL=24  # Cache for 24 hours
ENABLE_CACHING=true  # Enable Redis caching
```

**For High Throughput:**
```env
PROCESSING_MODE=async
MAX_CONCURRENT_PAGES=5
WORKERS=4
```

## 📈 Monitoring

### **Health Checks**
- **Basic**: `GET /ping`
- **Detailed**: `GET /health/enhanced`
- **Configuration**: `GET /config`
- **Application Info**: `GET /info`

### **Metrics**
- Response times for each processor
- Cache hit rates
- API usage statistics
- Error rates and types

## 🔮 Advanced Usage

### **Custom Gemini Configuration**
```env
GEMINI_MODEL=pro  # Use Gemini Pro for better quality
GEMINI_CACHE_TTL=48  # Cache for 48 hours
```

### **Custom Tavily Configuration**
```env
TAVILY_SEARCH_DEPTH=advanced  # More thorough search
TAVILY_MAX_RESULTS=10  # More results per search
```

### **Hybrid Processing**
```env
PROCESSING_MODE=hybrid  # Smart selection based on document size
```

## 💡 Best Practices

1. **Use Enhanced Mode** for best results with Gemini + Tavily
2. **Enable caching** for better performance
3. **Monitor API usage** to stay within limits
4. **Use Auto mode** for automatic fallbacks
5. **Test with your documents** to optimize settings

## 🎉 Success Criteria

Your enhanced setup is successful when:

1. ✅ `/health/enhanced` shows all services healthy
2. ✅ Document processing uses `gemini_tavily` method
3. ✅ Search returns AI-generated summaries
4. ✅ Caching improves subsequent requests
5. ✅ Related content includes academic and video sources

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Run `python test_enhanced_features.py`
3. Check `/health/enhanced` endpoint
4. Verify API keys and quotas
5. Review application logs

---

**Enjoy the enhanced SmartRead experience! 🚀**
