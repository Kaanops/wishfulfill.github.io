from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime
import uuid

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.wishplatform
wishes_collection = db.wishes

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class WishCreate(BaseModel):
    title: str
    description: str
    amount_needed: float
    currency: str
    creator_name: str
    creator_email: str
    creator_paypal: Optional[str] = None

class Wish(BaseModel):
    id: str
    title: str
    description: str
    amount_needed: float
    currency: str
    creator_name: str
    creator_email: str
    creator_paypal: Optional[str] = None
    created_at: datetime
    status: str = "active"
    donations_received: float = 0.0

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "wish-platform"}

@app.post("/api/wishes", response_model=Wish)
async def create_wish(wish: WishCreate):
    wish_dict = wish.dict()
    wish_dict["id"] = str(uuid.uuid4())
    wish_dict["created_at"] = datetime.utcnow()
    wish_dict["status"] = "active"
    wish_dict["donations_received"] = 0.0
    
    result = wishes_collection.insert_one(wish_dict)
    
    # Return the created wish
    created_wish = wishes_collection.find_one({"_id": result.inserted_id})
    created_wish["_id"] = str(created_wish["_id"])
    
    return Wish(**created_wish)

@app.get("/api/wishes", response_model=List[Wish])
async def get_wishes(limit: int = 50):
    wishes = list(wishes_collection.find({}).sort("created_at", -1).limit(limit))
    
    for wish in wishes:
        wish["_id"] = str(wish["_id"])
    
    return [Wish(**wish) for wish in wishes]

@app.get("/api/wishes/{wish_id}", response_model=Wish)
async def get_wish(wish_id: str):
    wish = wishes_collection.find_one({"id": wish_id})
    
    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")
    
    wish["_id"] = str(wish["_id"])
    return Wish(**wish)

@app.put("/api/wishes/{wish_id}/donate")
async def donate_to_wish(wish_id: str, amount: float):
    wish = wishes_collection.find_one({"id": wish_id})
    
    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")
    
    # Update donations received
    new_amount = wish.get("donations_received", 0) + amount
    wishes_collection.update_one(
        {"id": wish_id},
        {"$set": {"donations_received": new_amount}}
    )
    
    return {"message": "Donation recorded", "new_total": new_amount}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)