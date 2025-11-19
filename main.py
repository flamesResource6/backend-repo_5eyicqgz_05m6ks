import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal

from database import db, create_document, get_documents
from schemas import Property, BULGARIAN_REGIONS

app = FastAPI(title="Bulghousing API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EUR_TO_BGN = 1.95583

class CreatePropertyRequest(Property):
    pass

class SearchResponse(BaseModel):
    results: List[dict]
    total: int

@app.get("/")
def read_root():
    return {"message": "Bulghousing backend running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

@app.post("/api/properties")
def create_property(payload: CreatePropertyRequest):
    data = payload.model_dump()
    # normalize currency and compute both EUR/BGN for fast filtering
    cur = data.get("currency", "EUR")
    price_value = data["price_value"]
    if cur == "EUR":
        price_eur = price_value
        price_bgn = price_value * EUR_TO_BGN
    else:
        price_bgn = price_value
        price_eur = price_value / EUR_TO_BGN
    data["price_eur"] = round(price_eur, 2)
    data["price_bgn"] = round(price_bgn, 2)

    inserted_id = create_document("property", data)
    return {"id": inserted_id}

@app.get("/api/properties")
def search_properties(
    q: Optional[str] = Query(None, description="Free text in title/description/address"),
    region: Optional[Literal[tuple(BULGARIAN_REGIONS)]] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    price_currency: Optional[Literal["EUR", "BGN"]] = Query("EUR"),
    min_sqm: Optional[float] = Query(None, ge=0),
    max_sqm: Optional[float] = Query(None, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    # Build mongo filter
    mongo_filter = {}

    # text search across a few fields
    if q:
        mongo_filter["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"address": {"$regex": q, "$options": "i"}},
        ]

    if region:
        mongo_filter["region"] = region

    # price filter on the normalized fields
    price_field = "price_eur" if price_currency == "EUR" else "price_bgn"
    price_range = {}
    if min_price is not None:
        price_range["$gte"] = float(min_price)
    if max_price is not None:
        price_range["$lte"] = float(max_price)
    if price_range:
        mongo_filter[price_field] = price_range

    # size filter
    size_range = {}
    if min_sqm is not None:
        size_range["$gte"] = float(min_sqm)
    if max_sqm is not None:
        size_range["$lte"] = float(max_sqm)
    if size_range:
        mongo_filter["size_sqm"] = size_range

    docs = get_documents("property", mongo_filter, limit)

    def shape(doc):
        # remove _id for cleanliness
        d = {k: v for k, v in doc.items() if k != "_id"}
        return d

    results = [shape(d) for d in docs]
    return {"results": results, "total": len(results)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
