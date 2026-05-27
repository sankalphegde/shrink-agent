import pandas as pd
import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

FIVETRAN_AUTH = HTTPBasicAuth(
    os.getenv("FIVETRAN_API_KEY"),
    os.getenv("FIVETRAN_API_SECRET")
)
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client["shrink_agent"]

def check_fivetran_status() -> dict:
    """Check Fivetran data pipeline status to ensure store data is fresh and synced."""
    try:
        response = requests.get("https://api.fivetran.com/v1/connectors", auth=FIVETRAN_AUTH)
        data = response.json()
        connectors = data.get("data", {}).get("items", [])
        return {
            "status": "connected",
            "connector_count": len(connectors),
            "message": f"Fivetran pipeline active. {len(connectors)} connector(s) found."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_recent_voids(hours_back: int = 8) -> dict:
    """
    Get recent unapproved void transactions from the store.
    Returns suspicious void patterns grouped by employee.

    Args:
        hours_back: How many hours back to look (default 8 hours)
    """
    df = pd.read_csv("data/returns_voids.csv", parse_dates=["timestamp"])
    cutoff = df["timestamp"].max() - timedelta(hours=hours_back)
    recent = df[
        (df["timestamp"] >= cutoff) &
        (df["manager_approved"] == "No") &
        (df["amount"] >= 15.0)
    ]
    if recent.empty:
        return {"suspicious_voids": [], "message": "No suspicious voids found"}
    grouped = []
    for emp_id, group in recent.groupby("employee_id"):
        grouped.append({
            "employee_id": emp_id,
            "register_id": group["register_id"].iloc[0],
            "void_count": len(group),
            "total_amount": round(group["amount"].sum(), 2),
            "items": list(group["item_name"]),
            "timestamps": list(group["timestamp"].astype(str))
        })
    return {
        "suspicious_voids": grouped,
        "total_found": len(grouped),
        "message": f"Found {len(grouped)} employee(s) with suspicious void patterns"
    }

def get_inventory_status(sku: str) -> dict:
    """
    Check inventory levels for a specific SKU to detect unexplained stock drops.

    Args:
        sku: The SKU code to check (e.g. SKU-8821)
    """
    df = pd.read_csv("data/inventory.csv", parse_dates=["timestamp"])
    item_data = df[df["sku"] == sku].sort_values("timestamp")
    if item_data.empty:
        return {"found": False, "message": f"SKU {sku} not found"}
    latest = item_data.iloc[-1]
    drops = item_data[item_data["delta"] < -1]
    return {
        "found": True,
        "sku": sku,
        "item_name": latest["item_name"],
        "zone": latest["zone"],
        "latest_expected": int(latest["expected_qty"]),
        "latest_actual": int(latest["actual_qty"]),
        "latest_delta": int(latest["delta"]),
        "unexplained_drops": len(drops),
        "message": f"{'⚠️ Inventory drop detected' if latest['delta'] < -1 else '✅ Inventory normal'}"
    }

def get_camera_events(zone: str, hours_back: int = 8) -> dict:
    """
    Check camera metadata for loitering or suspicious activity in a store zone.

    Args:
        zone: Store zone to check (e.g. 'Aisle 7', 'Exit', 'Liquor')
        hours_back: How many hours back to look
    """
    df = pd.read_csv("data/camera_metadata.csv", parse_dates=["timestamp"])
    cutoff = df["timestamp"].max() - timedelta(hours=hours_back)
    zone_events = df[(df["zone"] == zone) & (df["timestamp"] >= cutoff)]
    loitering = zone_events[
        (zone_events["event_type"] == "LOITER") &
        (zone_events["dwell_seconds"] >= 300)
    ]
    return {
        "zone": zone,
        "total_events": len(zone_events),
        "loitering_events": len(loitering),
        "max_dwell_seconds": int(loitering["dwell_seconds"].max()) if not loitering.empty else 0,
        "suspicious": len(loitering) > 0,
        "message": f"{'⚠️ Loitering detected' if not loitering.empty else '✅ No suspicious activity'} in {zone}"
    }

def save_incident(
    employee_id: str,
    register_id: str,
    store_id: str,
    risk_tier: str,
    signals: str,
    total_amount: float,
    alert_text: str
) -> dict:
    """
    Save a confirmed suspicious incident to the database for staff review.

    Args:
        employee_id: Employee ID involved
        register_id: Register where voids occurred
        store_id: Store identifier
        risk_tier: Risk level - LOW, MEDIUM, or HIGH
        signals: Comma-separated list of signals detected
        total_amount: Total dollar amount of suspicious voids
        alert_text: Plain English alert for store staff
    """
    doc = {
        "employee_id": employee_id,
        "register_id": register_id,
        "store_id": store_id,
        "risk_tier": risk_tier,
        "signals": signals.split(","),
        "total_void_amount": total_amount,
        "alert_text": alert_text,
        "status": "OPEN",
        "created_at": datetime.utcnow(),
        "source": "adk_agent"
    }
    result = db["incidents"].insert_one(doc)
    return {
        "saved": True,
        "incident_id": str(result.inserted_id),
        "message": "✅ Incident saved. Staff review required."
    }