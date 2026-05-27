import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.correlator import correlate
from agent.scorer import score_incident
from agent.alerter import generate_alert
from db.incidents import save_incident

def run():
    print("\n🔍 Shrink Agent starting...\n")

    print("Step 1: Correlating events across data sources...")
    incidents = correlate()
    print(f"         Found {len(incidents)} suspicious incident(s)\n")

    if not incidents:
        print("✅ No anomalies detected. Store looks clean.")
        return

    print("Step 2: Scoring incidents...")
    scored = [score_incident(inc) for inc in incidents]

    print("Step 3: Generating Gemini alerts...")
    alerted = [generate_alert(s) for s in scored]

    print("Step 4: Saving to MongoDB...\n")
    for inc in alerted:
        incident_id = save_incident(inc)
        print(f"🚨 ALERT SAVED")
        print(f"   ID       : {incident_id}")
        print(f"   Store    : {inc['store_id']}")
        print(f"   Employee : {inc['employee_id']}")
        print(f"   Risk     : {inc['risk_tier']} ({inc['score']}/100)")
        print(f"   Alert    : {inc['alert_text'][:100]}...")
        print()

    print(f"✅ Done. {len(alerted)} alert(s) saved. Open the dashboard to review.")

if __name__ == "__main__":
    run()