# SmartRead Makefile

.PHONY: help setup install start stop test clean

# Default target
help:
	@echo "SmartRead Development Commands"
	@echo "=============================="
	@echo "setup     - Initial setup (install dependencies, create env files)"
	@echo "install   - Install dependencies only"
	@echo "start     - Start all services (databases + backend + frontend)"
	@echo "start-db  - Start only databases"
	@echo "start-api - Start only backend API"
	@echo "start-web - Start only frontend"
	@echo "stop      - Stop all services"
	@echo "test      - Run improvement tests"
	@echo "clean     - Clean up containers and volumes"
	@echo "logs      - Show logs from all services"
	@echo "status    - Show status of all services"

# Setup everything
setup:
	@echo "🚀 Setting up SmartRead..."
	chmod +x setup.sh
	./setup.sh

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
	cd web && npm install

# Start all services
start:
	@echo "🚀 Starting all services..."
	docker-compose up -d
	@echo "Waiting for databases to be ready..."
	@sleep 10
	@echo "Starting backend..."
	cd backend && source .venv/bin/activate && python main_improved.py &
	@echo "Starting frontend..."
	cd web && npm run dev &
	@echo "✅ All services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"

# Start only databases
start-db:
	@echo "🗄️ Starting databases..."
	docker-compose up -d mongodb redis
	@echo "✅ Databases started!"

# Start only backend
start-api:
	@echo "🔧 Starting backend API..."
	cd backend && source .venv/bin/activate && python main_improved.py

# Start only frontend
start-web:
	@echo "🌐 Starting frontend..."
	cd web && npm run dev

# Stop all services
stop:
	@echo "🛑 Stopping all services..."
	docker-compose down
	@pkill -f "python main" || true
	@pkill -f "npm run dev" || true
	@echo "✅ All services stopped!"

# Run tests
test:
	@echo "🧪 Running improvement tests..."
	python3 test_improvements.py

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Cleanup completed!"

# Show logs
logs:
	@echo "📋 Showing logs..."
	docker-compose logs -f

# Show status
status:
	@echo "📊 Service Status:"
	@echo "=================="
	@echo "Docker containers:"
	@docker-compose ps
	@echo ""
	@echo "Backend health:"
	@curl -s http://localhost:8000/ping || echo "Backend not responding"
	@echo ""
	@echo "Frontend health:"
	@curl -s http://localhost:3000 > /dev/null && echo "Frontend responding" || echo "Frontend not responding"

# Development helpers
dev-backend:
	@echo "🔧 Starting backend in development mode..."
	cd backend && source .venv/bin/activate && ENVIRONMENT=development python main_improved.py

dev-frontend:
	@echo "🌐 Starting frontend in development mode..."
	cd web && npm run dev

# Database management
db-reset:
	@echo "🗄️ Resetting databases..."
	docker-compose down -v
	docker-compose up -d mongodb redis
	@echo "✅ Databases reset!"

# Backup database
db-backup:
	@echo "💾 Backing up database..."
	docker exec smartread-mongodb mongodump --db smartread --out /tmp/backup
	docker cp smartread-mongodb:/tmp/backup ./backup
	@echo "✅ Database backed up to ./backup"

# Restore database
db-restore:
	@echo "📥 Restoring database..."
	docker cp ./backup smartread-mongodb:/tmp/backup
	docker exec smartread-mongodb mongorestore --db smartread /tmp/backup/smartread
	@echo "✅ Database restored!"

# Check environment
check-env:
	@echo "🔍 Checking environment..."
	@echo "Python version: $(shell python3 --version)"
	@echo "Node version: $(shell node --version)"
	@echo "Docker version: $(shell docker --version)"
	@echo "Docker Compose version: $(shell docker-compose --version)"
	@echo ""
	@echo "Environment files:"
	@test -f backend/.env && echo "✅ backend/.env exists" || echo "❌ backend/.env missing"
	@test -f web/.env.local && echo "✅ web/.env.local exists" || echo "❌ web/.env.local missing"

# Performance test
perf-test:
	@echo "⚡ Running performance tests..."
	@echo "Testing response time..."
	@time curl -X POST "http://localhost:8000/api/extract" \
		-H "Content-Type: application/json" \
		-d '{"url": "https://arxiv.org/pdf/2301.07041.pdf", "page_number": 1}' \
		> /dev/null 2>&1 || echo "Performance test failed"

# Monitor resources
monitor:
	@echo "📊 Monitoring resources..."
	@echo "Docker container stats:"
	@docker stats --no-stream
	@echo ""
	@echo "System resources:"
	@top -l 1 | head -10 || htop -n 1 || echo "Resource monitoring not available"
