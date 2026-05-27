import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["shrink_agent"]
collection = db["incidents"]

def save_incident(alerted_incident):
    """Save a fully processed incident to MongoDB"""
    doc = {
        **alerted_incident,
        "status": "OPEN",
        "created_at": datetime.utcnow(),
        "reviewed_by": None,
        "review_action": None
    }
    result = collection.insert_one(doc)
    return str(result.inserted_id)

def get_all_incidents():
    """Fetch all incidents sorted by most recent"""
    incidents = list(collection.find().sort("created_at", -1))
    for inc in incidents:
        inc["_id"] = str(inc["_id"])
    return incidents

def update_incident_status(incident_id, action):
    """Mark incident as confirmed theft or false alarm"""
    from bson import ObjectId
    collection.update_one(
        {"_id": ObjectId(incident_id)},
        {"$set": {
            "status": action,
            "reviewed_at": datetime.utcnow()
        }}
    )

if __name__ == "__main__":
    from agent.correlator import correlate
    from agent.scorer import score_incident
    from agent.alerter import generate_alert

    incidents = correlate()
    print(f"\n💾 Saving {len(incidents)} incident(s) to MongoDB...\n")

    for inc in incidents:
        scored = score_incident(inc)
        alerted = generate_alert(scored)
        incident_id = save_incident(alerted)
        print(f"✅ Saved incident: {incident_id}")
        print(f"   Employee : {alerted['employee_id']}")
        print(f"   Risk     : {alerted['risk_tier']}")
        print(f"   Alert    : {alerted['alert_text'][:80]}...")