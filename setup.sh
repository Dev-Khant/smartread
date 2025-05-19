#!/bin/bash

# SmartRead Setup Script
echo "🚀 Setting up SmartRead with improvements..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
else
    print_warning "Unsupported platform: $OSTYPE"
    PLATFORM="Unknown"
fi

print_status "Detected platform: $PLATFORM"

# 1. Check Prerequisites
print_status "Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js found: $NODE_VERSION"
else
    print_error "Node.js not found. Please install Node.js 18 or higher."
    exit 1
fi

# Check Docker (optional)
if command -v docker &> /dev/null; then
    print_status "Docker found: $(docker --version)"
    DOCKER_AVAILABLE=true
else
    print_warning "Docker not found. You'll need to install MongoDB and Redis manually."
    DOCKER_AVAILABLE=false
fi

# 2. Setup Backend
print_status "Setting up backend..."

cd backend

# Create virtual environment
if [ ! -d ".venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment file
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please edit backend/.env with your actual API keys and configuration"
else
    print_status ".env file already exists"
fi

cd ..

# 3. Setup Frontend
print_status "Setting up frontend..."

cd web

# Install dependencies
print_status "Installing Node.js dependencies..."
npm install

# Setup environment file
if [ ! -f ".env.local" ]; then
    print_status "Creating frontend .env.local file..."
    echo "NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000" > .env.local
    print_status "Frontend environment file created"
else
    print_status "Frontend .env.local file already exists"
fi

cd ..

# 4. Setup Databases (if Docker is available)
if [ "$DOCKER_AVAILABLE" = true ]; then
    print_status "Setting up databases with Docker..."
    
    # Create docker-compose.yml for databases
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  mongodb:
    image: mongo:7
    container_name: smartread-mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: smartread
    volumes:
      - mongodb_data:/data/db
    networks:
      - smartread-network

  redis:
    image: redis:7-alpine
    container_name: smartread-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - smartread-network

volumes:
  mongodb_data:
  redis_data:

networks:
  smartread-network:
    driver: bridge
EOF

    print_status "Starting databases..."
    docker-compose up -d
    
    # Wait for databases to be ready
    print_status "Waiting for databases to be ready..."
    sleep 10
    
    # Check if databases are running
    if docker-compose ps | grep -q "Up"; then
        print_status "Databases are running successfully!"
    else
        print_error "Failed to start databases. Check docker-compose logs."
    fi
else
    print_warning "Please install MongoDB and Redis manually:"
    echo "  MongoDB: https://docs.mongodb.com/manual/installation/"
    echo "  Redis: https://redis.io/download"
fi

# 5. Create startup scripts
print_status "Creating startup scripts..."

# Backend startup script
cat > start-backend.sh << 'EOF'
#!/bin/bash
cd backend
source .venv/bin/activate

# Check if we should use the improved version
if [ "$1" = "improved" ]; then
    echo "Starting improved backend with async routes..."
    python main_improved.py
else
    echo "Starting original backend..."
    python main.py
fi
EOF

chmod +x start-backend.sh

# Frontend startup script
cat > start-frontend.sh << 'EOF'
#!/bin/bash
cd web
npm run dev
EOF

chmod +x start-frontend.sh

# Combined startup script
cat > start-all.sh << 'EOF'
#!/bin/bash

# Start databases if Docker is available
if command -v docker-compose &> /dev/null; then
    echo "Starting databases..."
    docker-compose up -d
    sleep 5
fi

# Start backend in background
echo "Starting backend..."
./start-backend.sh improved &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 5

# Start frontend
echo "Starting frontend..."
./start-frontend.sh &
FRONTEND_PID=$!

echo "🚀 SmartRead is starting up!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Access the application at: http://localhost:3000"
echo "API documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap 'echo "Stopping services..."; kill $BACKEND_PID $FRONTEND_PID; exit' INT
wait
EOF

chmod +x start-all.sh

# 6. Create testing script
cat > test-setup.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing SmartRead setup..."

# Test backend health
echo "Testing backend health..."
if curl -s http://localhost:8000/ping > /dev/null; then
    echo "✅ Backend is responding"
else
    echo "❌ Backend is not responding"
fi

# Test database connections
echo "Testing database connections..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Databases are connected"
else
    echo "❌ Database connection issues"
fi

# Test frontend
echo "Testing frontend..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is responding"
else
    echo "❌ Frontend is not responding"
fi

echo "Test completed!"
EOF

chmod +x test-setup.sh

# 7. Final instructions
print_status "Setup completed! 🎉"
echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env with your API keys:"
echo "   - MISTRAL_API_KEY"
echo "   - GROQ_API_KEY"
echo "   - CLOUDINARY credentials"
echo "   - SERPER_API_KEY (optional, for search)"
echo ""
echo "2. Start the application:"
echo "   ./start-all.sh"
echo ""
echo "3. Or start services individually:"
echo "   ./start-backend.sh improved  # For improved version"
echo "   ./start-frontend.sh"
echo ""
echo "4. Test the setup:"
echo "   ./test-setup.sh"
echo ""
echo "🌐 URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo ""
print_warning "Don't forget to configure your API keys in backend/.env!"
