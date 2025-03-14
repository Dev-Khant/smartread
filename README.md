# SmartRead

A modern web application with a Next.js frontend and FastAPI backend.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git (for cloning the repository)

## Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd smartread
```

2. Set up environment variables:

For the backend (`/backend/.env`):
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

For the frontend (`/web/.env.local`):
```bash
cp web/.env.example web/.env.local
# Edit web/.env.local with your configuration
```

## Running the Application

### Using Individual Docker Images

#### Backend (FastAPI)
```bash
# Build the backend image
cd backend
docker build -t smartread-backend .

# Run in development mode (with hot reload)
docker run -p 8000:8000 \
  --env-file .env \
  -v $(pwd):/app \
  -v /app/__pycache__ \
  smartread-backend

# Run in production mode
docker run -p 8000:8000 \
  --env-file .env \
  -e ENVIRONMENT=production \
  smartread-backend
```

#### Frontend (Next.js)
```bash
# Build the frontend image
cd web
docker build -t smartread-frontend .

# Run in development mode
docker run -p 3000:3000 \
  --env-file .env.local \
  -v $(pwd):/app \
  -v /app/node_modules \
  -v /app/.next \
  smartread-frontend

# Run in production mode
docker run -p 3000:3000 \
  --env-file .env.local \
  -e NODE_ENV=production \
  smartread-frontend
```

### Running Locally (Without Docker)

#### Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (Next.js)
```bash
cd web
npm install
npm run dev
```

## Development

- The backend runs on Python 3.12 with FastAPI
- The frontend is built with Next.js and TypeScript
- MongoDB is used as the database (in development mode)
- Hot-reload is enabled for both frontend and backend in development mode

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Environment Variables

### Backend Variables (`.env`)
```plaintext
PORT=8000                    # API port
HOST=0.0.0.0                # API host
ENVIRONMENT=development      # development/production
MONGODB_URL=mongodb://...    # MongoDB connection URL
MISTRAL_API_KEY=            # Mistral AI API key
GROQ_API_KEY=               # Groq API key
CLOUDINARY_*                # Cloudinary configuration
```

### Frontend Variables (`.env.local`)
```plaintext
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000  # Backend API URL
```
