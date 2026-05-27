import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FIVETRAN_API_KEY")
API_SECRET = os.getenv("FIVETRAN_API_SECRET")
BASE_URL = "https://api.fivetran.com/v1"
auth = HTTPBasicAuth(API_KEY, API_SECRET)

def list_connectors():
    """List all Fivetran connectors in the account"""
    response = requests.get(f"{BASE_URL}/connectors", auth=auth)
    data = response.json()
    return data.get("data", {}).get("items", [])

def get_connector_status(connector_id):
    """Get sync status of a specific connector"""
    response = requests.get(f"{BASE_URL}/connectors/{connector_id}", auth=auth)
    return response.json().get("data", {})

def trigger_sync(connector_id):
    """Trigger a manual sync for a connector"""
    response = requests.post(
        f"{BASE_URL}/connectors/{connector_id}/sync",
        auth=auth
    )
    return response.json()

if __name__ == "__main__":
    print("🔌 Connecting to Fivetran...\n")
    connectors = list_connectors()
    if connectors:
        print(f"Found {len(connectors)} connector(s):")
        for c in connectors:
            print(f"  - {c['id']} | {c['service']} | status: {c['status']['sync_state']}")
    else:
        print("No connectors found — account connected successfully ✅")