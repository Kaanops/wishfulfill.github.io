from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime, timedelta
import uuid
import random

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.wishplatform
wishes_collection = db.wishes
success_stories_collection = db.success_stories

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Categories
WISH_CATEGORIES = [
    "Education", "Health", "Emergency", "Business", "Travel", 
    "Technology", "Family", "Community", "Creative", "Other"
]

# Pydantic models
class WishCreate(BaseModel):
    title: str
    description: str
    amount_needed: float
    currency: str
    creator_name: str
    creator_email: str
    creator_paypal: Optional[str] = None
    category: str
    urgency: str = "medium"  # low, medium, high
    photo_url: Optional[str] = None

class Wish(BaseModel):
    id: str
    title: str
    description: str
    amount_needed: float
    currency: str
    creator_name: str
    creator_email: str
    creator_paypal: Optional[str] = None
    category: str
    urgency: str
    photo_url: Optional[str] = None
    created_at: datetime
    status: str = "active"  # active, fulfilled, cancelled
    donations_received: float = 0.0
    donor_count: int = 0
    fulfillment_percentage: float = 0.0

class SuccessStory(BaseModel):
    id: str
    title: str
    description: str
    amount_fulfilled: float
    currency: str
    fulfillment_date: datetime
    donor_count: int
    photo_url: str
    category: str

# Initialize with demo success stories
def init_success_stories():
    if success_stories_collection.count_documents({}) == 0:
        demo_stories = [
            {
                "id": str(uuid.uuid4()),
                "title": "Medical Treatment for Maria's Surgery",
                "description": "Thanks to 15 generous donors, Maria received the life-saving surgery she needed. She's now fully recovered and back to her studies.",
                "amount_fulfilled": 8500.0,
                "currency": "EUR",
                "fulfillment_date": datetime.utcnow() - timedelta(days=45),
                "donor_count": 15,
                "photo_url": "https://images.unsplash.com/photo-1559757148-5c350d0d3c56",
                "category": "Health"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Lisa's Dream University Education",
                "description": "Lisa's dream of studying computer science came true when 23 donors helped fund her tuition. She just graduated with honors!",
                "amount_fulfilled": 12000.0,
                "currency": "EUR",
                "fulfillment_date": datetime.utcnow() - timedelta(days=120),
                "donor_count": 23,
                "photo_url": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f",
                "category": "Education"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Emergency Rent for Single Mother",
                "description": "Within 48 hours, 8 kind strangers helped prevent Sarah and her children from becoming homeless. They're now stable and thriving.",
                "amount_fulfilled": 2800.0,
                "currency": "EUR",
                "fulfillment_date": datetime.utcnow() - timedelta(days=30),
                "donor_count": 8,
                "photo_url": "https://images.unsplash.com/photo-1519834785169-98be25ec3f84",
                "category": "Emergency"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Community Garden Project",
                "description": "Local residents came together to fund a community garden that now feeds 50 families weekly. Amazing teamwork!",
                "amount_fulfilled": 5200.0,
                "currency": "EUR",
                "fulfillment_date": datetime.utcnow() - timedelta(days=90),
                "donor_count": 31,
                "photo_url": "https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg",
                "category": "Community"
            }
        ]
        success_stories_collection.insert_many(demo_stories)

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "wish-platform"}

@app.get("/api/categories")
async def get_categories():
    return {"categories": WISH_CATEGORIES}

@app.get("/api/statistics")
async def get_statistics():
    # Calculate real statistics
    total_wishes = wishes_collection.count_documents({})
    fulfilled_wishes = wishes_collection.count_documents({"status": "fulfilled"}) + 4  # Include demo stories
    total_raised = list(wishes_collection.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$donations_received"}}}
    ]))
    total_amount = (total_raised[0]["total"] if total_raised else 0) + 28500  # Include demo amounts
    
    return {
        "total_wishes": total_wishes + 4,
        "fulfilled_wishes": fulfilled_wishes,
        "total_raised": total_amount,
        "success_rate": round((fulfilled_wishes / max(total_wishes + 4, 1)) * 100, 1)
    }

@app.get("/api/success-stories", response_model=List[SuccessStory])
async def get_success_stories():
    stories = list(success_stories_collection.find({}).sort("fulfillment_date", -1))
    for story in stories:
        story["_id"] = str(story["_id"])
    return [SuccessStory(**story) for story in stories]

@app.post("/api/wishes", response_model=Wish)
async def create_wish(wish: WishCreate):
    wish_dict = wish.dict()
    wish_dict["id"] = str(uuid.uuid4())
    wish_dict["created_at"] = datetime.utcnow()
    wish_dict["status"] = "active"
    wish_dict["donations_received"] = 0.0
    wish_dict["donor_count"] = 0
    wish_dict["fulfillment_percentage"] = 0.0
    
    result = wishes_collection.insert_one(wish_dict)
    
    # Return the created wish
    created_wish = wishes_collection.find_one({"_id": result.inserted_id})
    created_wish["_id"] = str(created_wish["_id"])
    
    return Wish(**created_wish)

@app.get("/api/wishes", response_model=List[Wish])
async def get_wishes(
    limit: int = 50,
    category: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    status: str = "active"
):
    query = {"status": status}
    if category and category != "All":
        query["category"] = category
    if urgency:
        query["urgency"] = urgency
        
    wishes = list(wishes_collection.find(query).sort("created_at", -1).limit(limit))
    
    for wish in wishes:
        wish["_id"] = str(wish["_id"])
        # Add default values for missing fields (backward compatibility)
        if "category" not in wish:
            wish["category"] = "Other"
        if "urgency" not in wish:
            wish["urgency"] = "medium"
        if "photo_url" not in wish:
            wish["photo_url"] = None
        # Calculate fulfillment percentage
        if wish["amount_needed"] > 0:
            wish["fulfillment_percentage"] = min(100, (wish["donations_received"] / wish["amount_needed"]) * 100)
    
    return [Wish(**wish) for wish in wishes]

@app.get("/api/wishes/{wish_id}", response_model=Wish)
async def get_wish(wish_id: str):
    wish = wishes_collection.find_one({"id": wish_id})
    
    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")
    
    wish["_id"] = str(wish["_id"])
    if wish["amount_needed"] > 0:
        wish["fulfillment_percentage"] = min(100, (wish["donations_received"] / wish["amount_needed"]) * 100)
    
    return Wish(**wish)

@app.put("/api/wishes/{wish_id}/donate")
async def donate_to_wish(wish_id: str, amount: float):
    wish = wishes_collection.find_one({"id": wish_id})
    
    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")
    
    # Update donations received
    new_amount = wish.get("donations_received", 0) + amount
    new_donor_count = wish.get("donor_count", 0) + 1
    fulfillment_percentage = min(100, (new_amount / wish["amount_needed"]) * 100)
    
    # Update status if fully funded
    new_status = "fulfilled" if fulfillment_percentage >= 100 else "active"
    
    wishes_collection.update_one(
        {"id": wish_id},
        {"$set": {
            "donations_received": new_amount,
            "donor_count": new_donor_count,
            "fulfillment_percentage": fulfillment_percentage,
            "status": new_status
        }}
    )
    
    return {
        "message": "Donation recorded",
        "new_total": new_amount,
        "fulfillment_percentage": fulfillment_percentage,
        "status": new_status
    }

# Initialize success stories on startup
@app.on_event("startup")
async def startup_event():
    init_success_stories()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)