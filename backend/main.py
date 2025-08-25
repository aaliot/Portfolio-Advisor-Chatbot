import yfinance as yf
import sqlite3
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import pandas as pd
from dataclasses import dataclass

# =====================================================================
# 1. DATA MODELS: define the structure of the input data and internal entitiies the chatbot uses
# =====================================================================

class UserInput(BaseModel): #represents a chat message from the user
    message: str #the content of the user's message
    user_id: str = "default_user" #the ID of the user sending the message

class PortfolioHolding(BaseModel): #represents a stock holding in the user's portfolio
    symbol: str 
    quantity: float
    buy_price: float
    buy_date: str

class AlertSetting(BaseModel): #represents a price alert set by the user
    symbol: str
    condition: str  # "above", "below"
    price: float
    active: bool = True

@dataclass
class Intent: #represents the interpreted intent of the user's message
    action: str  # "show_portfolio", "add_alert", "compare_stocks", "simulate", "add_holding"
    entities: Dict #the entities extracted from the user's message like stock symbols and quantities
    confidence: float #estimates how sure the model is about the intent

# =====================================================================
# 2. DATABASE LAYER: separates the storage logic from business logic, ensures all data is persisted and retrieval
# =====================================================================

class PortfolioDatabase:
    def __init__(self, db_path: str = "portfolio.db"): #initialize the database connection and create tables
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Holdings table: stores user stocks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                symbol TEXT,
                quantity REAL,
                buy_price REAL,
                buy_date TEXT,
                UNIQUE(user_id, symbol)
            )
        """)
        
        # Alerts table: stores price alerts for each stock
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                symbol TEXT,
                condition TEXT,
                price REAL,
                active BOOLEAN,
                created_date TEXT
            )
        """)
        
        # Transaction log: logs all buy/sell actions for history/auditing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                symbol TEXT,
                action TEXT,
                quantity REAL,
                price REAL,
                date TEXT
            )
        """)
        
        conn.commit()
        conn.close()

    # inserts a new stock holding to the user's portfolio and logs the transaction
    def add_holding(self, user_id: str, symbol: str, quantity: float, buy_price: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO holdings (user_id, symbol, quantity, buy_price, buy_date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, symbol, quantity, buy_price, datetime.now().isoformat()))
        
        # Log transaction
        cursor.execute("""
            INSERT INTO transactions (user_id, symbol, action, quantity, price, date)
            VALUES (?, ?, 'BUY', ?, ?, ?)
        """, (user_id, symbol, quantity, buy_price, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    # retrieves the user's current portfolio holdings
    def get_portfolio(self, user_id: str) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol, quantity, buy_price, buy_date 
            FROM holdings 
            WHERE user_id = ?
        """, (user_id,))
        
        holdings = []
        for row in cursor.fetchall():
            holdings.append({
                "symbol": row[0],
                "quantity": row[1],
                "buy_price": row[2],
                "buy_date": row[3]
            })
        
        conn.close()
        return holdings

    # adds a new price alert for a stock
    def add_alert(self, user_id: str, symbol: str, condition: str, price: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alerts (user_id, symbol, condition, price, active, created_date)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (user_id, symbol, condition, price, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    # retrieves all active price alerts for a user
    def get_alerts(self, user_id: str) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol, condition, price, active 
            FROM alerts 
            WHERE user_id = ? AND active = 1
        """, (user_id,))
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                "symbol": row[0],
                "condition": row[1],
                "price": row[2],
                "active": bool(row[3])
            })
        
        conn.close()
        return alerts

# =====================================================================
# 3. NLP & COMMAND PROCESSOR: interprets user messages, extracts intents and entities, into structured instructions
# =====================================================================

class NLPProcessor:
    def __init__(self):
        self.intent_patterns = { #map user input patterns(regex) to intents
            "show_portfolio": [
                r"show.*portfolio", r"my.*holdings", r"portfolio.*summary",
                r"what.*do.*i.*own", r"current.*portfolio"
            ],
            "add_alert": [
                r"alert.*me.*if", r"notify.*when", r"tell.*me.*if",
                r"set.*alert", r"watch.*for"
            ],
            "compare_stocks": [
                r"compare.*vs", r"compare.*and", r".*vs.*",
                r"difference.*between", r"which.*better"
            ],
            "simulate": [
                r"what.*if.*buy", r"simulate.*buying", r"if.*i.*bought",
                r"scenario.*where", r"what.*would.*happen"
            ],
            "add_holding": [
                r"i.*bought", r"add.*to.*portfolio", r"i.*own",
                r"purchased.*shares", r"bought.*shares"
            ],
            "stock_price": [
                r"price.*of", r"current.*price", r"how.*much.*is",
                r"what.*is.*trading", r".*price.*now"
            ]
        }
    
    def extract_entities(self, text: str) -> Dict:
        entities = {}
        
        # Extract stock symbols (3-4 letter uppercase)
        symbols = re.findall(r'\b[A-Z]{2,4}\b', text.upper())
        if symbols:
            entities['symbols'] = symbols
        
        # Extract numbers (quantities, prices)
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            entities['numbers'] = [float(n) for n in numbers]
        
        # Extract comparison words
        if any(word in text.lower() for word in ['above', 'over', 'higher']):
            entities['condition'] = 'above'
        elif any(word in text.lower() for word in ['below', 'under', 'lower']):
            entities['condition'] = 'below'
        
        return entities

    # matches the input text to an intent
    # returns an Intent object with action, entities, and confidence
    def classify_intent(self, text: str) -> Intent:
        text_lower = text.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    entities = self.extract_entities(text)
                    return Intent(
                        action=intent,
                        entities=entities,
                        confidence=0.8
                    )
        
        # Default intent
        entities = self.extract_entities(text)
        return Intent(
            action="stock_price",
            entities=entities,
            confidence=0.5
        )

# =====================================================================
# 4. MARKET DATA API: fetches real-time and historical market data
# =====================================================================

class MarketDataAPI:
    @staticmethod
    def get_stock_info(symbol: str) -> Dict:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="1d")
            
            if hist.empty:
                return {"error": f"No data found for {symbol}"}
            
            current_price = hist['Close'].iloc[-1]
            
            return {
                "symbol": symbol,
                "name": info.get("shortName", "N/A"),
                "current_price": round(current_price, 2),
                "currency": info.get("currency", "USD"),
                "sector": info.get("sector", "N/A"),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "day_change": round(hist['Close'].iloc[-1] - hist['Open'].iloc[-1], 2) if len(hist) > 0 else 0
            }
        except Exception as e:
            return {"error": f"Error fetching data for {symbol}: {str(e)}"}
    
    @staticmethod
    def get_historical_data(symbol: str, period: str = "1mo") -> Dict:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            
            return {
                "symbol": symbol,
                "period": period,
                "data": hist.to_dict('records')[-10:]  # Last 10 records
            }
        except Exception as e:
            return {"error": f"Error fetching historical data: {str(e)}"}

# =====================================================================
# 5. ANALYTICS ENGINE: performs calculations and simulations on portfolio data
# =====================================================================

class AnalyticsEngine:
    def __init__(self, db: PortfolioDatabase, market_api: MarketDataAPI):
        self.db = db
        self.market_api = market_api
    
    # loops through user holdings, gets live prices from marketdatapi, and then calculates
    def calculate_portfolio_value(self, user_id: str) -> Dict: 
        holdings = self.db.get_portfolio(user_id)
        
        if not holdings:
            return {"message": "No holdings found in portfolio"}
        
        total_value = 0
        total_cost = 0
        portfolio_details = []
        
        for holding in holdings:
            stock_info = self.market_api.get_stock_info(holding['symbol'])
            
            if 'error' in stock_info:
                continue
                
            current_value = holding['quantity'] * stock_info['current_price']
            cost_basis = holding['quantity'] * holding['buy_price']
            profit_loss = current_value - cost_basis
            
            portfolio_details.append({
                "symbol": holding['symbol'],
                "name": stock_info['name'],
                "quantity": holding['quantity'],
                "buy_price": holding['buy_price'],
                "current_price": stock_info['current_price'],
                "current_value": round(current_value, 2),
                "cost_basis": round(cost_basis, 2),
                "profit_loss": round(profit_loss, 2),
                "profit_loss_pct": round((profit_loss / cost_basis) * 100, 2) if cost_basis > 0 else 0
            })
            
            total_value += current_value
            total_cost += cost_basis
        
        total_profit_loss = total_value - total_cost
        
        return {
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_profit_loss": round(total_profit_loss, 2),
            "total_profit_loss_pct": round((total_profit_loss / total_cost) * 100, 2) if total_cost > 0 else 0,
            "holdings": portfolio_details
        }
    
    def compare_stocks(self, symbols: List[str]) -> Dict:
        comparison = {}
        
        for symbol in symbols:
            stock_info = self.market_api.get_stock_info(symbol)
            if 'error' not in stock_info:
                comparison[symbol] = stock_info
        
        return {"comparison": comparison}
    
    def simulate_purchase(self, user_id: str, symbol: str, quantity: float) -> Dict:
        stock_info = self.market_api.get_stock_info(symbol)
        
        if 'error' in stock_info:
            return stock_info
        
        current_portfolio = self.calculate_portfolio_value(user_id)
        purchase_cost = quantity * stock_info['current_price']
        
        return {
            "simulation": {
                "symbol": symbol,
                "quantity": quantity,
                "price_per_share": stock_info['current_price'],
                "total_cost": round(purchase_cost, 2),
                "current_portfolio_value": current_portfolio.get('total_value', 0),
                "new_portfolio_value": round(current_portfolio.get('total_value', 0) + purchase_cost, 2)
            }
        }

# =====================================================================
# 6. MAIN APPLICATION: defines API endpoints and request handling
# =====================================================================

app = FastAPI(title="Portfolio Chatbot API", version="1.0.0")

# CORS middleware (enables cross origin requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = PortfolioDatabase()
nlp = NLPProcessor()
market_api = MarketDataAPI()
analytics = AnalyticsEngine(db, market_api)

@app.post("/chat")
async def chat_endpoint(user_input: UserInput):
    """Main chatbot endpoint that processes natural language commands"""
    
    # Process the message through NLP
    intent = nlp.classify_intent(user_input.message)
    
    try:
        # Route to appropriate handler based on intent
        if intent.action == "show_portfolio":
            response = analytics.calculate_portfolio_value(user_input.user_id)
            
        elif intent.action == "add_alert":
            if 'symbols' in intent.entities and 'numbers' in intent.entities and 'condition' in intent.entities:
                symbol = intent.entities['symbols'][0]
                price = intent.entities['numbers'][0]
                condition = intent.entities['condition']
                db.add_alert(user_input.user_id, symbol, condition, price)
                response = {"message": f"Alert set for {symbol} when price goes {condition} ${price}"}
            else:
                response = {"message": "Please specify symbol, price, and condition (above/below)"}
                
        elif intent.action == "compare_stocks":
            if 'symbols' in intent.entities and len(intent.entities['symbols']) >= 2:
                symbols = intent.entities['symbols'][:2]  # Compare first 2 symbols
                response = analytics.compare_stocks(symbols)
            else:
                response = {"message": "Please specify at least 2 stock symbols to compare"}
                
        elif intent.action == "simulate":
            if 'symbols' in intent.entities and 'numbers' in intent.entities:
                symbol = intent.entities['symbols'][0]
                quantity = intent.entities['numbers'][0]
                response = analytics.simulate_purchase(user_input.user_id, symbol, quantity)
            else:
                response = {"message": "Please specify symbol and quantity for simulation"}
                
        elif intent.action == "add_holding":
            if 'symbols' in intent.entities and len(intent.entities['numbers']) >= 2:
                symbol = intent.entities['symbols'][0]
                quantity = intent.entities['numbers'][0]
                price = intent.entities['numbers'][1]
                db.add_holding(user_input.user_id, symbol, quantity, price)
                response = {"message": f"Added {quantity} shares of {symbol} at ${price} to portfolio"}
            else:
                response = {"message": "Please specify symbol, quantity, and purchase price"}
                
        elif intent.action == "stock_price":
            if 'symbols' in intent.entities:
                symbol = intent.entities['symbols'][0]
                stock_info = market_api.get_stock_info(symbol)
                response = {"stock_info": stock_info}
            else:
                response = {"message": "Please specify a stock symbol"}
                
        else:
            response = {"message": "I didn't understand that command. Try asking about your portfolio, setting alerts, or comparing stocks."}
    
    except Exception as e:
        response = {"error": f"An error occurred: {str(e)}"}
    
    return {
        "intent": {
            "action": intent.action,
            "entities": intent.entities,
            "confidence": intent.confidence
        },
        "response": response
    }

@app.get("/portfolio/{user_id}")
async def get_portfolio(user_id: str):
    """Get portfolio summary for a user"""
    return analytics.calculate_portfolio_value(user_id)

@app.get("/alerts/{user_id}")
async def get_alerts(user_id: str):
    """Get active alerts for a user"""
    return {"alerts": db.get_alerts(user_id)}

@app.get("/stock/{symbol}")
async def get_stock_info(symbol: str):
    """Get current information for a stock"""
    return market_api.get_stock_info(symbol)

# Keep your original recommendation endpoint for backward compatibility
@app.post("/recommend")
def recommend_portfolio(input: UserInput):
    # This is your original simple recommendation logic
    risk_level = "medium"  # default
    
    if "low" in input.message.lower():
        tickers = ["AAPL", "JNJ"]
        weights = [0.4, 0.6]
    elif "high" in input.message.lower():
        tickers = ["TSLA", "NVDA"]
        weights = [0.5, 0.5]
    else:
        tickers = ["AAPL", "TSLA", "JNJ"]
        weights = [0.3, 0.4, 0.3]
    
    portfolio = []
    for ticker, weight in zip(tickers, weights):
        info = market_api.get_stock_info(ticker)
        info["allocation"] = weight
        portfolio.append(info)
    
    return {"portfolio": portfolio}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)