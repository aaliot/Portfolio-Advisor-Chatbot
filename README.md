📈 AI Portfolio Advisor

An interactive portfolio recommendation chatbot built with FastAPI, yFinance, and React.
It helps users, especially beginner investors, get stock allocation suggestions based on their risk level and investment amount.

This project demonstrates:

⚡ Full-stack engineering (FastAPI backend + React frontend)

📊 Real-time financial data integration (via yFinance
)

🤖 AI-style chatbot interface for better UX

🔒 CORS handling and structured API design with FastAPI

🚀 Features

✅ Risk-based Portfolio Suggestions – Users choose low, medium, or high risk, and get a recommended stock allocation.
✅ Investment Scaling – Enter an amount (e.g., £10,000) and see exact stock allocations.
✅ Live Market Data – Fetches real stock prices using yFinance to calculate allocations.
✅ API-Driven Architecture – Clean backend endpoints, easy to extend for more asset classes.
✅ Frontend Chatbot UI – Users interact as if they’re talking to a financial assistant.

🏗️ Tech Stack

Backend: FastAPI
 (Python)

Frontend: React + Vite

Data Source: Yahoo Finance (via yfinance)

Validation: Pydantic

Deployment Ready: Can run locally or be hosted on Render, Heroku, or Vercel.

📂 Project Structure
portfolio-advisor/
│── backend/
│   ├── main.py         # FastAPI app (portfolio recommendation logic)
│   ├── requirements.txt # Dependencies
│
│── frontend/
│   ├── src/
│   │   ├── App.jsx     # Chatbot UI
│   │   ├── api.js      # API calls to backend
│   └── package.json    # Frontend dependencies
│
│── README.md

⚙️ Installation & Setup
1️⃣ Backend (FastAPI)
cd backend
python -m venv venv
source venv/bin/activate   # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
uvicorn main:app --reload


By default, API runs at: http://127.0.0.1:8000

2️⃣ Frontend (React + Vite)
cd frontend
npm install
npm run dev


Frontend runs at: http://localhost:5173

📌 API Example

POST /recommend

Request:

{
  "risk_level": "medium",
  "investment": 10000
}


Response:

{
  "portfolio": {
    "AAPL": 3000,
    "TSLA": 4000,
    "JNJ": 3000
  }
}

💡 Future Enhancements

🤝 Add ETF and crypto support

📊 Display portfolio growth simulations

🔔 Add notifications for price changes

🧠 Use ML to recommend personalized portfolios

📚 Why This Project?

This isn’t just a toy project—it mimics real-world fintech apps like Nutmeg, Wealthfront, or Betterment.
It shows off:

Your ability to build full-stack apps

Comfort with APIs & data pipelines

Knowledge of finance + tech integration

Perfect for a portfolio piece when applying for software engineering, fintech, or data-driven roles.

✨ Built by Aaliyah – exploring the intersection of AI, finance, and software engineering.