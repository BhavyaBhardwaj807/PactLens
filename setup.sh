#!/bin/bash
# PactLens Setup Script

echo "🚀 PactLens Setup"
echo "================="

# Check Python
echo "✓ Checking Python..."
python3 --version

# Setup Backend
echo ""
echo "📦 Setting up Backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✓ Backend dependencies installed"

# Create .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
    echo "  ⚠️  Please edit .env and add your OpenAI API key"
fi

cd ..

# Setup Frontend
echo ""
echo "📦 Setting up Frontend..."
cd frontend
npm install
echo "✓ Frontend dependencies installed"

cd ..

echo ""
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your LLM key"
echo "2. Run backend: cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload"
echo "3. Run frontend: cd frontend && npm run dev"
echo "4. Open http://localhost:5173"
