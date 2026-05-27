import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("AIzaSyARgbiCXQPEnz1GNG3LPIjmuvKULRqpNDs")
)

def generate_alert(scored_incident):
    prompt = f"""
You are a retail loss prevention AI assistant.

Analyze the following suspicious incident and write a clear, concise alert for store staff.
The alert should:
- State what happened and when
- List the suspicious signals detected
- Give a risk level
- Recommend a specific action for staff
- Be professional, factual, and avoid accusatory language
- Be under 100 words

Incident data:
- Store: {scored_incident['store_id']}
- Employee ID: {scored_incident['employee_id']}
- Register: {scored_incident['register_id']}
- Time window: {scored_incident['window_start']} to {scored_incident['window_end']}
- Number of unapproved voids: {scored_incident['void_count']}
- Total void amount: ${scored_incident['total_void_amount']}
- Items involved: {scored_incident['items_involved']}
- Inventory drop confirmed: {scored_incident['inventory_drop']}
- Loitering detected: {scored_incident['loitering_detected']}
- Signals: {scored_incident['signals']}
- Risk score: {scored_incident['score']}/100
- Risk tier: {scored_incident['risk_tier']}

Write the alert now:
"""

    response = client.models.generate_content(
model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        **scored_incident,
        "alert_text": response.text,
        "alert_generated": True
    }

if __name__ == "__main__":
    from correlator import correlate
    from scorer import score_incident

    incidents = correlate()
    print(f"\n🚨 Generating alerts for {len(incidents)} incident(s):\n")
    print("=" * 60)

    for inc in incidents:
        scored = score_incident(inc)
        alerted = generate_alert(scored)
        print(f"RISK: {alerted['risk_tier']} | Score: {alerted['score']}/100")
        print(f"Store: {alerted['store_id']} | Employee: {alerted['employee_id']} | Register: {alerted['register_id']}")
        print(f"Time: {alerted['window_start']}")
        print()
        print(alerted['alert_text'])
        print("=" * 60)