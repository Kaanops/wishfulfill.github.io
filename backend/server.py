from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from datetime import datetime, timedelta
import uuid
import paypalrestsdk
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.wishplatform
wishes_collection = db.wishes
success_stories_collection = db.success_stories
payment_transactions_collection = db.payment_transactions

# PayPal Configuration
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
PAYPAL_ENVIRONMENT = os.environ.get('PAYPAL_ENVIRONMENT', 'sandbox')

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": PAYPAL_ENVIRONMENT,
    "client_id": PAYPAL_CLIENT_ID,
    "client_secret": PAYPAL_CLIENT_SECRET
})

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Categories and constants
WISH_CATEGORIES = [
    "Education", "Health", "Emergency", "Business", "Travel", 
    "Technology", "Family", "Community", "Creative", "Other"
]

POSTING_FEE = 2.0  # Fixed 2€ posting fee

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
    urgency: str = "medium"
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
    status: str = "active"
    donations_received: float = 0.0
    donor_count: int = 0
    fulfillment_percentage: float = 0.0
    payment_status: str = "pending"  # pending, paid, failed

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

class PaymentRequest(BaseModel):
    amount: float
    currency: str
    purpose: str  # "posting_fee" or "donation"
    wish_id: Optional[str] = None
    return_url: str
    cancel_url: str

class PaymentTransaction(BaseModel):
    id: str
    payment_id: str
    session_id: Optional[str] = None
    amount: float
    currency: str
    purpose: str
    wish_id: Optional[str] = None
    payer_email: Optional[str] = None
    status: str  # pending, completed, failed, cancelled
    created_at: datetime
    updated_at: datetime

# Helper functions
def get_paypal_access_token():
    """Get PayPal access token for API calls"""
    url = f"https://api.{PAYPAL_ENVIRONMENT}.paypal.com/v1/oauth2/token"
    
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en_US',
    }
    
    data = 'grant_type=client_credentials'
    
    response = requests.post(
        url, 
        headers=headers, 
        data=data, 
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
    )
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise HTTPException(status_code=500, detail="Failed to get PayPal access token")

def create_paypal_payment(amount: float, currency: str, return_url: str, cancel_url: str, description: str):
    """Create PayPal payment"""
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": return_url,
            "cancel_url": cancel_url
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": description,
                    "sku": "001",
                    "price": str(amount),
                    "currency": currency.upper(),
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(amount),
                "currency": currency.upper()
            },
            "description": description
        }]
    })
    
    if payment.create():
        return payment
    else:
        raise HTTPException(status_code=500, detail=f"PayPal payment creation failed: {payment.error}")

def execute_paypal_payment(payment_id: str, payer_id: str):
    """Execute PayPal payment after user approval"""
    payment = paypalrestsdk.Payment.find(payment_id)
    
    if payment.execute({"payer_id": payer_id}):
        return payment
    else:
        raise HTTPException(status_code=500, detail=f"PayPal payment execution failed: {payment.error}")

# Initialize demo success stories
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
    return {"status": "healthy", "service": "wish-platform", "payments": "paypal"}

@app.get("/api/categories")
async def get_categories():
    return {"categories": WISH_CATEGORIES}

@app.get("/api/statistics")
async def get_statistics():
    # Calculate real statistics
    total_wishes = wishes_collection.count_documents({})
    fulfilled_wishes = wishes_collection.count_documents({"status": "fulfilled"}) + 4
    
    # Get total from paid wishes only
    paid_wishes = list(wishes_collection.find({"payment_status": "paid"}))
    total_raised = sum([wish.get("donations_received", 0) for wish in paid_wishes]) + 28500
    
    return {
        "total_wishes": total_wishes + 4,
        "fulfilled_wishes": fulfilled_wishes,
        "total_raised": total_raised,
        "success_rate": round((fulfilled_wishes / max(total_wishes + 4, 1)) * 100, 1),
        "posting_fee": POSTING_FEE
    }

@app.get("/api/success-stories", response_model=List[SuccessStory])
async def get_success_stories():
    stories = list(success_stories_collection.find({}).sort("fulfillment_date", -1))
    for story in stories:
        story["_id"] = str(story["_id"])
    return [SuccessStory(**story) for story in stories]

# Payment endpoints
@app.post("/api/payments/create")
async def create_payment(payment_request: PaymentRequest):
    """Create a PayPal payment"""
    try:
        # Validate amount
        if payment_request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        # Create description based on purpose
        if payment_request.purpose == "posting_fee":
            description = f"Wish Posting Fee (€{POSTING_FEE})"
            # Override amount for posting fee
            payment_request.amount = POSTING_FEE
        else:
            description = f"Donation for Wish"
        
        # Create PayPal payment
        payment = create_paypal_payment(
            amount=payment_request.amount,
            currency=payment_request.currency,
            return_url=payment_request.return_url,
            cancel_url=payment_request.cancel_url,
            description=description
        )
        
        # Save transaction to database
        transaction_id = str(uuid.uuid4())
        transaction = {
            "id": transaction_id,
            "payment_id": payment.id,
            "amount": payment_request.amount,
            "currency": payment_request.currency,
            "purpose": payment_request.purpose,
            "wish_id": payment_request.wish_id,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        payment_transactions_collection.insert_one(transaction)
        
        # Get approval URL
        approval_url = None
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = link.href
                break
        
        return {
            "payment_id": payment.id,
            "transaction_id": transaction_id,
            "approval_url": approval_url,
            "status": "created"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")

@app.post("/api/payments/execute")
async def execute_payment(payment_id: str, payer_id: str):
    """Execute PayPal payment after user approval"""
    try:
        # Find transaction
        transaction = payment_transactions_collection.find_one({"payment_id": payment_id})
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Execute payment
        payment = execute_paypal_payment(payment_id, payer_id)
        
        # Update transaction status
        payment_transactions_collection.update_one(
            {"payment_id": payment_id},
            {"$set": {
                "status": "completed",
                "payer_email": payment.payer.payer_info.email if payment.payer.payer_info else None,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # If this was a posting fee, mark the wish as paid
        if transaction["purpose"] == "posting_fee" and transaction.get("wish_id"):
            wishes_collection.update_one(
                {"id": transaction["wish_id"]},
                {"$set": {"payment_status": "paid"}}
            )
        
        # If this was a donation, update the wish
        elif transaction["purpose"] == "donation" and transaction.get("wish_id"):
            wish = wishes_collection.find_one({"id": transaction["wish_id"]})
            if wish:
                new_amount = wish.get("donations_received", 0) + transaction["amount"]
                new_donor_count = wish.get("donor_count", 0) + 1
                fulfillment_percentage = min(100, (new_amount / wish["amount_needed"]) * 100)
                
                # Update status if fully funded
                new_status = "fulfilled" if fulfillment_percentage >= 100 else "active"
                
                wishes_collection.update_one(
                    {"id": transaction["wish_id"]},
                    {"$set": {
                        "donations_received": new_amount,
                        "donor_count": new_donor_count,
                        "fulfillment_percentage": fulfillment_percentage,
                        "status": new_status
                    }}
                )
        
        return {
            "status": "completed",
            "payment_id": payment_id,
            "transaction_id": transaction["id"]
        }
        
    except Exception as e:
        # Update transaction as failed
        payment_transactions_collection.update_one(
            {"payment_id": payment_id},
            {"$set": {
                "status": "failed",
                "updated_at": datetime.utcnow()
            }}
        )
        raise HTTPException(status_code=500, detail=f"Payment execution failed: {str(e)}")

@app.get("/api/payments/status/{payment_id}")
async def get_payment_status(payment_id: str):
    """Get payment status"""
    transaction = payment_transactions_collection.find_one({"payment_id": payment_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Clean up MongoDB ObjectId
    transaction["_id"] = str(transaction["_id"])
    
    return {
        "payment_id": payment_id,
        "transaction_id": transaction["id"],
        "status": transaction["status"],
        "amount": transaction["amount"],
        "currency": transaction["currency"],
        "purpose": transaction["purpose"],
        "created_at": transaction["created_at"],
        "updated_at": transaction["updated_at"]
    }

# Existing wish endpoints with payment integration
@app.post("/api/wishes", response_model=Wish)
async def create_wish(wish: WishCreate):
    """Create a new wish (payment will be handled separately)"""
    wish_dict = wish.dict()
    wish_dict["id"] = str(uuid.uuid4())
    wish_dict["created_at"] = datetime.utcnow()
    wish_dict["status"] = "active"
    wish_dict["donations_received"] = 0.0
    wish_dict["donor_count"] = 0
    wish_dict["fulfillment_percentage"] = 0.0
    wish_dict["payment_status"] = "pending"  # Will be updated after payment
    
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
    status: str = "active",
    paid_only: bool = True
):
    query = {"status": status}
    
    # Only show paid wishes by default (unless specifically requesting all)
    if paid_only:
        query["payment_status"] = "paid"
    
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
        if "payment_status" not in wish:
            wish["payment_status"] = "pending"
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
    # Add default values for missing fields
    if "payment_status" not in wish:
        wish["payment_status"] = "pending"
    if "category" not in wish:
        wish["category"] = "Other"
    if "urgency" not in wish:
        wish["urgency"] = "medium"
    if "photo_url" not in wish:
        wish["photo_url"] = None
        
    if wish["amount_needed"] > 0:
        wish["fulfillment_percentage"] = min(100, (wish["donations_received"] / wish["amount_needed"]) * 100)
    
    return Wish(**wish)

# Legacy donation endpoint (now redirects to payment system)
@app.put("/api/wishes/{wish_id}/donate")
async def donate_to_wish(wish_id: str, amount: float):
    """Legacy endpoint - now returns payment instructions"""
    wish = wishes_collection.find_one({"id": wish_id})
    
    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")
    
    return {
        "message": "Please use the new payment system",
        "payment_endpoint": "/api/payments/create",
        "amount": amount,
        "wish_id": wish_id,
        "purpose": "donation"
    }

# Initialize success stories on startup
@app.on_event("startup")
async def startup_event():
    init_success_stories()
    print(f"PayPal configured for {PAYPAL_ENVIRONMENT} environment")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)