# 📊 Portfolio Chatbot

An AI-powered investment assistant that builds personalized stock portfolios based on user **risk tolerance** and **investment amount**.  
The app suggests stocks, shows portfolio allocations, and visualizes performance with interactive charts.

---

## 🚀 Features

- ✅ Chatbot interface for portfolio recommendations  
- ✅ User inputs: **risk level** & **investment amount**  
- ✅ Portfolio allocation with sector breakdown  
- ✅ Interactive chart visualization (Recharts)  
- ✅ Real-time stock data (via [Yahoo Finance](https://pypi.org/project/yfinance/))  
- ✅ Backend powered by **FastAPI**  
- ✅ Frontend built with **React + TailwindCSS**  

---

## 🛠️ Tech Stack

**Frontend**  
- React  
- TailwindCSS  
- Recharts  

**Backend**  
- FastAPI (Python)  
- yfinance (Yahoo Finance API wrapper)  

---

## ⚡ Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/portfolio-chatbot.git
cd portfolio-chatbot
2. Backend setup
bash
Copy
Edit
cd backend
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

pip install -r requirements.txt
uvicorn main:app --reload
The backend runs at: http://127.0.0.1:8000

3. Frontend setup
bash
Copy
Edit
cd frontend
npm install
npm run dev
The frontend runs at: http://localhost:5173

📂 Project Structure
plaintext
Copy
Edit
portfolio-chatbot/
│
├── backend/                  # FastAPI backend
│   ├── main.py                # API endpoints
│   ├── portfolio.py           # Portfolio logic
│   ├── requirements.txt       # Python dependencies
│
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── App.jsx            # Main app
│   │   ├── components/        # Reusable UI components
│   │   ├── assets/            # Images/icons
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md

💡 Future Enhancements

🤝 Add ETF and crypto support

📊 Display portfolio growth simulations

🔔 Add notifications for price changes

🧠 Use ML to recommend personalized portfolios


