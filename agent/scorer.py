def score_incident(incident):
    """
    Score an incident based on number and type of signals.
    Returns risk tier and confidence score.
    """
    score = 0

    # Signal 1: Multiple unapproved voids
    if incident["void_count"] >= 3:
        score += 40
    elif incident["void_count"] == 2:
        score += 25

    # Signal 2: High void amount
    if incident["total_void_amount"] >= 100:
        score += 25
    elif incident["total_void_amount"] >= 50:
        score += 15

    # Signal 3: Inventory drop confirmed
    if incident["inventory_drop"]:
        score += 25

    # Signal 4: Loitering detected
    if incident["loitering_detected"]:
        score += 10

    # Determine risk tier
    if score >= 70:
        risk_tier = "HIGH"
    elif score >= 40:
        risk_tier = "MEDIUM"
    else:
        risk_tier = "LOW"

    return {
        **incident,
        "score": score,
        "risk_tier": risk_tier
    }

if __name__ == "__main__":
    from correlator import correlate

    incidents = correlate()
    print(f"\n📊 Scoring {len(incidents)} incident(s):\n")

    for inc in incidents:
        scored = score_incident(inc)
        print(f"  Employee : {scored['employee_id']}")
        print(f"  Register : {scored['register_id']}")
        print(f"  Amount   : ${scored['total_void_amount']}")
        print(f"  Score    : {scored['score']}/100")
        print(f"  Risk     : {scored['risk_tier']}")
        print()