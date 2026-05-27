import pandas as pd
from datetime import datetime, timedelta

# Time window to correlate events (5 minutes)
CORRELATION_WINDOW_MINUTES = 5

# Minimum void amount to be considered suspicious
SUSPICIOUS_VOID_AMOUNT = 15.00

# Minimum dwell time to be considered loitering (seconds)
LOITER_THRESHOLD_SECONDS = 300

def load_data():
    """Load all 4 data sources"""
    transactions = pd.read_csv("data/transactions.csv", parse_dates=["timestamp"])
    voids        = pd.read_csv("data/returns_voids.csv", parse_dates=["timestamp"])
    camera       = pd.read_csv("data/camera_metadata.csv", parse_dates=["timestamp"])
    inventory    = pd.read_csv("data/inventory.csv", parse_dates=["timestamp"])
    return transactions, voids, camera, inventory

def find_void_bursts(voids):
    """
    Find employees with multiple unapproved voids
    within a short time window — strongest theft signal
    """
    suspicious = voids[
        (voids["manager_approved"] == "No") &
        (voids["amount"] >= SUSPICIOUS_VOID_AMOUNT)
    ].copy()

    clusters = []
    employees = suspicious["employee_id"].unique()

    for emp in employees:
        emp_voids = suspicious[suspicious["employee_id"] == emp].sort_values("timestamp")

        if len(emp_voids) < 2:
            continue

        # Slide a 5-minute window
        for i, row in emp_voids.iterrows():
            window_end = row["timestamp"] + timedelta(minutes=CORRELATION_WINDOW_MINUTES)
            window_voids = emp_voids[
                (emp_voids["timestamp"] >= row["timestamp"]) &
                (emp_voids["timestamp"] <= window_end)
            ]

            if len(window_voids) >= 2:
                clusters.append({
                    "employee_id": emp,
                    "register_id": row["register_id"],
                    "store_id": row["store_id"],
                    "window_start": row["timestamp"],
                    "window_end": window_end,
                    "void_count": len(window_voids),
                    "total_void_amount": round(window_voids["amount"].sum(), 2),
                    "items_voided": list(window_voids["item_name"]),
                    "skus_voided": list(window_voids["sku"])
                })
                break  # One cluster per employee per window

    return clusters

def find_inventory_drops(inventory, window_start, window_end, skus):
    """
    Check if inventory dropped for any of the voided SKUs
    around the same time window
    """
    drops = inventory[
        (inventory["sku"].isin(skus)) &
        (inventory["timestamp"] >= window_start - timedelta(minutes=10)) &
        (inventory["timestamp"] <= window_end + timedelta(minutes=10)) &
        (inventory["delta"] < 0)
    ]
    return drops

def find_loitering(camera, store_id, window_start, window_end):
    """
    Check if camera detected loitering near the time of voids
    """
    loiters = camera[
        (camera["store_id"] == store_id) &
        (camera["event_type"] == "LOITER") &
        (camera["dwell_seconds"] >= LOITER_THRESHOLD_SECONDS) &
        (camera["timestamp"] >= window_start - timedelta(minutes=10)) &
        (camera["timestamp"] <= window_end + timedelta(minutes=10))
    ]
    return loiters

def correlate():
    """
    Main correlation function.
    Returns a list of suspicious incidents with all corroborating signals.
    """
    transactions, voids, camera, inventory = load_data()

    void_clusters = find_void_bursts(voids)
    incidents = []

    for cluster in void_clusters:
        inv_drops = find_inventory_drops(
            inventory,
            cluster["window_start"],
            cluster["window_end"],
            cluster["skus_voided"]
        )

        loiters = find_loitering(
            camera,
            cluster["store_id"],
            cluster["window_start"],
            cluster["window_end"]
        )

        signals = []
        if cluster["void_count"] >= 2:
            signals.append(f"{cluster['void_count']} unapproved voids in 5 minutes")
        if not inv_drops.empty:
            signals.append(f"inventory drop detected for {list(inv_drops['item_name'])}")
        if not loiters.empty:
            signals.append(f"loitering detected in {list(loiters['zone'])} for {list(loiters['dwell_seconds'])}s")

        if len(signals) >= 2:
            incidents.append({
                "store_id": cluster["store_id"],
                "employee_id": cluster["employee_id"],
                "register_id": cluster["register_id"],
                "window_start": str(cluster["window_start"]),
                "window_end": str(cluster["window_end"]),
                "void_count": cluster["void_count"],
                "total_void_amount": cluster["total_void_amount"],
                "items_involved": cluster["items_voided"],
                "inventory_drop": not inv_drops.empty,
                "loitering_detected": not loiters.empty,
                "loiter_zones": list(loiters["zone"]) if not loiters.empty else [],
                "signals": signals,
                "signal_count": len(signals)
            })

    return incidents

if __name__ == "__main__":
    incidents = correlate()
    print(f"\n🔍 Correlation complete. Found {len(incidents)} suspicious incident(s):\n")
    for i, inc in enumerate(incidents, 1):
        print(f"Incident {i}:")
        print(f"  Store    : {inc['store_id']}")
        print(f"  Employee : {inc['employee_id']}")
        print(f"  Register : {inc['register_id']}")
        print(f"  Time     : {inc['window_start']}")
        print(f"  Signals  : {inc['signals']}")
        print(f"  Amount   : ${inc['total_void_amount']}")
        print()