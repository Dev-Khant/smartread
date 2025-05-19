#!/bin/bash

# Test script for all SmartRead versions
echo "🧪 Testing All SmartRead Versions"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Test function
test_version() {
    local version_name=$1
    local main_file=$2
    local port=$3
    
    print_header "Testing $version_name"
    
    # Start the server in background
    cd backend
    source .venv/bin/activate
    python $main_file &
    SERVER_PID=$!
    cd ..
    
    # Wait for server to start
    sleep 5
    
    # Test health endpoint
    if curl -s http://localhost:$port/ping > /dev/null; then
        print_status "$version_name: Health check passed"
        
        # Test PDF extraction
        print_status "$version_name: Testing PDF extraction..."
        response=$(curl -s -X POST "http://localhost:$port/api/extract" \
            -H "Content-Type: application/json" \
            -d '{"url": "https://arxiv.org/pdf/2301.07041.pdf", "page_number": 1}')
        
        if echo "$response" | grep -q "success\|processing"; then
            print_status "$version_name: PDF extraction test passed"
        else
            print_error "$version_name: PDF extraction test failed"
        fi
    else
        print_error "$version_name: Health check failed"
    fi
    
    # Stop the server
    kill $SERVER_PID
    sleep 2
    
    echo ""
}

# Ensure backend dependencies are installed
print_status "Checking backend dependencies..."
cd backend
if [ ! -d ".venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install regular requirements
if [ -f "requirements.txt" ]; then
    print_status "Installing regular requirements..."
    pip install -q -r requirements.txt
fi

# Install no-cloudinary requirements
if [ -f "requirements_no_cloudinary.txt" ]; then
    print_status "Installing no-cloudinary requirements..."
    pip install -q -r requirements_no_cloudinary.txt
fi

cd ..

# Test all versions
print_header "Starting version tests..."

# Test 1: Original version
if [ -f "backend/main.py" ]; then
    test_version "Original Version" "main.py" 8000
else
    print_warning "Original version (main.py) not found"
fi

# Test 2: Improved version
if [ -f "backend/main_improved.py" ]; then
    test_version "Improved Version" "main_improved.py" 8000
else
    print_warning "Improved version (main_improved.py) not found"
fi

# Test 3: No Cloudinary version
if [ -f "backend/main_no_cloudinary.py" ]; then
    test_version "No Cloudinary Version" "main_no_cloudinary.py" 8000
else
    print_warning "No Cloudinary version (main_no_cloudinary.py) not found"
fi

# Performance comparison
print_header "Performance Comparison"

echo "Version Comparison Summary:"
echo "=========================="
echo "1. Original Version:"
echo "   - Uses Cloudinary for all file storage"
echo "   - Synchronous processing"
echo "   - Basic error handling"
echo ""
echo "2. Improved Version:"
echo "   - Uses Cloudinary + Redis caching"
echo "   - Async processing"
echo "   - Enhanced error handling"
echo "   - Rate limiting"
echo ""
echo "3. No Cloudinary Version:"
echo "   - Local file storage"
echo "   - No external dependencies"
echo "   - Simplified setup"
echo "   - Cost-effective"
echo ""

# Storage comparison
print_header "Storage Comparison"

echo "Storage Options:"
echo "==============="
echo "Cloudinary:"
echo "  ✅ Automatic optimization"
echo "  ✅ Global CDN"
echo "  ✅ Zero maintenance"
echo "  ❌ Monthly costs"
echo "  ❌ External dependency"
echo ""
echo "Local Storage:"
echo "  ✅ No costs"
echo "  ✅ Full control"
echo "  ✅ No external dependencies"
echo "  ❌ No CDN"
echo "  ❌ Server storage limits"
echo ""

# Recommendations
print_header "Recommendations"

echo "Choose based on your needs:"
echo "=========================="
echo "🚀 For Development/Testing:"
echo "   → Use No Cloudinary Version"
echo "   → Fastest setup, no external dependencies"
echo ""
echo "📈 For Small Production:"
echo "   → Use No Cloudinary Version + Nginx"
echo "   → Cost-effective, good performance"
echo ""
echo "🌍 For Large Scale:"
echo "   → Use Improved Version with Cloudinary"
echo "   → Best performance, global CDN"
echo ""
echo "🔒 For Privacy/Control:"
echo "   → Use No Cloudinary Version + MinIO"
echo "   → Self-hosted, S3-compatible"
echo ""

print_status "All tests completed!"
echo ""
echo "Next steps:"
echo "1. Choose the version that fits your needs"
echo "2. Configure environment variables"
echo "3. Start the application"
echo "4. Test with your own PDFs"
