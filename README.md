# SmartRead

SmartRead is an AI-powered tool designed to automatically annotate technical PDFs, providing key insights and important highlights. Additionally, it offers related articles and videos to enhance understanding.


https://github.com/user-attachments/assets/3644033c-8953-4d22-8d32-697b60b28afe


## Features

- **Smart Annotation**: View key insights and important highlights from the PDF
- **Related Resources**: Get related articles and videos on selected technical highlights for improved understanding
- **Technical PDFs**: Works with any technical PDF, making technical reading easier to understand
- **Download Annotated PDF**: Save a copy of the annotated original PDF to keep highlights

## Technology Stack

- **Frontend**: Next.js with TypeScript
- **Backend**: FastAPI (Python 3.12)
- **Database**: MongoDB
- **AI Models**: Mistral AI and Groq
- **Storage**: Cloudinary
- **Containerization**: Docker (backend only)

## Getting Started

### Prerequisites

- Git
- Node.js 18+ (for frontend)
- Docker (for backend)
- Python 3.12 (for local backend development)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd smartread

# Set up environment variables
cp backend/.env.example backend/.env
cp web/.env.example web/.env.local
```

### Environment Setup

#### Backend Variables (.env)
```plaintext
PORT=8000                    # API port
HOST=0.0.0.0                # API host
ENVIRONMENT=development      # development/production
MONGODB_URL=mongodb://...    # MongoDB connection URL
MISTRAL_API_KEY=            # Mistral AI API key
GROQ_API_KEY=               # Groq API key
CLOUDINARY_CLOUD_NAME=      # Cloudinary cloud name
CLOUDINARY_API_KEY=         # Cloudinary API key
CLOUDINARY_API_SECRET=      # Cloudinary API secret
```

#### Frontend Variables (.env.local)
```plaintext
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000  # Backend API URL
```

### Running the Application

#### Frontend (Next.js)

```bash
# Navigate to frontend directory
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

#### Backend (FastAPI)

Using Docker:
```bash
cd backend
docker build -t smartread-backend .
docker run -p 8000:8000 --env-file .env smartread-backend
```

Or for local development:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Development

The application is built with:
- Next.js and TypeScript for the frontend
- FastAPI (Python 3.12) for the backend
- MongoDB for data storage
- Mistral and Groq AI models for AI features
- Cloudinary for media management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Installation Documentation](https://www.mongodb.com/docs/manual/installation/)
- [Cloudinary Documentation](https://cloudinary.com/documentation)
- [Mistral AI OCR Documentation](https://docs.mistral.ai/capabilities/document/)
- [Groq Documentation](https://console.groq.com/docs/overview)
