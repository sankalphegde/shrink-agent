import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os

fake = Faker()
random.seed(42)
np.random.seed(42)

# Constants
STORE_ID = "STORE-184"
NUM_DAYS = 7
START_DATE = datetime(2026, 5, 20)

EMPLOYEES = [f"E{i:03d}" for i in range(1, 11)]
REGISTERS = [f"R{i}" for i in range(1, 6)]
CAMERAS = {
    "Aisle 1": "CAM-01A", "Aisle 2": "CAM-02A", "Aisle 3": "CAM-03A",
    "Aisle 7": "CAM-07A", "Aisle 9": "CAM-09A", "Electronics": "CAM-EL1",
    "Liquor": "CAM-LQ1", "Pharmacy": "CAM-PH1", "Exit": "CAM-EX1", "Entrance": "CAM-EN1"
}

HIGH_VALUE_ITEMS = [
    {"sku": "SKU-8821", "name": "Gillette Fusion Razor 4pk", "price": 24.99, "zone": "Aisle 7"},
    {"sku": "SKU-4401", "name": "Jack Daniels 750ml", "price": 54.99, "zone": "Liquor"},
    {"sku": "SKU-2210", "name": "Chanel No.5 Perfume", "price": 89.99, "zone": "Aisle 3"},
    {"sku": "SKU-3301", "name": "Oral-B Electric Toothbrush", "price": 69.99, "zone": "Aisle 9"},
    {"sku": "SKU-5512", "name": "Duracell AA 20pk", "price": 19.99, "zone": "Aisle 1"},
    {"sku": "SKU-7723", "name": "Dove Men Care Gift Set", "price": 34.99, "zone": "Aisle 7"},
]

LOW_VALUE_ITEMS = [
    {"sku": "SKU-0011", "name": "Coca Cola 2L", "price": 2.99, "zone": "Aisle 2"},
    {"sku": "SKU-0022", "name": "Lay's Chips 200g", "price": 3.49, "zone": "Aisle 2"},
    {"sku": "SKU-0033", "name": "Bread Loaf", "price": 4.99, "zone": "Aisle 1"},
    {"sku": "SKU-0044", "name": "Milk 1 Gallon", "price": 5.99, "zone": "Aisle 1"},
]

def generate_normal_transactions(start_time, end_time, num=60):
    txns = []
    current = start_time
    for _ in range(num):
        item = random.choice(HIGH_VALUE_ITEMS + LOW_VALUE_ITEMS)
        current += timedelta(minutes=random.randint(1, 15))
        if current > end_time:
            break
        txns.append({
            "transaction_id": f"T{random.randint(10000,99999)}",
            "store_id": STORE_ID,
            "register_id": random.choice(REGISTERS),
            "employee_id": random.choice(EMPLOYEES),
            "timestamp": current.strftime("%Y-%m-%d %H:%M:%S"),
            "sku": item["sku"],
            "item_name": item["name"],
            "quantity": random.randint(1, 3),
            "price": item["price"],
            "transaction_type": "SALE",
            "is_anomaly": False
        })
    return txns

def generate_normal_voids(start_time, end_time, num=5):
    voids = []
    current = start_time
    for _ in range(num):
        item = random.choice(LOW_VALUE_ITEMS)
        current += timedelta(minutes=random.randint(30, 90))
        if current > end_time:
            break
        voids.append({
            "event_id": f"RV-{random.randint(1000,9999)}",
            "store_id": STORE_ID,
            "register_id": random.choice(REGISTERS),
            "employee_id": random.choice(EMPLOYEES),
            "timestamp": current.strftime("%Y-%m-%d %H:%M:%S"),
            "sku": item["sku"],
            "item_name": item["name"],
            "amount": item["price"],
            "event_type": random.choice(["VOID", "RETURN"]),
            "manager_approved": random.choice(["Yes", "Yes", "No"]),
            "is_anomaly": False
        })
    return voids

def generate_normal_camera(start_time, end_time, num=40):
    events = []
    current = start_time
    for _ in range(num):
        zone = random.choice(list(CAMERAS.keys()))
        current += timedelta(minutes=random.randint(1, 20))
        if current > end_time:
            break
        events.append({
            "event_id": f"CAM-{random.randint(1000,9999)}",
            "store_id": STORE_ID,
            "zone": zone,
            "camera_id": CAMERAS[zone],
            "timestamp": current.strftime("%Y-%m-%d %H:%M:%S"),
            "dwell_seconds": random.randint(30, 180),
            "motion_flag": random.choice([True, False]),
            "person_count": random.randint(0, 3),
            "event_type": random.choice(["PASS", "BROWSE", "CLEAR"]),
            "is_anomaly": False
        })
    return events

def generate_normal_inventory(timestamp):
    records = []
    for item in HIGH_VALUE_ITEMS:
        delta = random.choice([-1, 0, 0, 0, 1])
        expected = random.randint(8, 15)
        records.append({
            "record_id": f"INV-{random.randint(1000,9999)}",
            "store_id": STORE_ID,
            "sku": item["sku"],
            "item_name": item["name"],
            "zone": item["zone"],
            "expected_qty": expected,
            "actual_qty": expected + delta,
            "delta": delta,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "adjusted_by": "SYSTEM",
            "is_anomaly": False
        })
    return records

def plant_sweethearting(base_time, employee_id, register_id):
    """Sweethearting: cashier voids high-value items for a friend, inventory drops"""
    item1 = HIGH_VALUE_ITEMS[0]
    item2 = HIGH_VALUE_ITEMS[1]
    item3 = HIGH_VALUE_ITEMS[2]

    txns = [{
        "transaction_id": f"T{random.randint(10000,99999)}",
        "store_id": STORE_ID,
        "register_id": register_id,
        "employee_id": employee_id,
        "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S"),
        "sku": item1["sku"], "item_name": item1["name"],
        "quantity": 1, "price": item1["price"],
        "transaction_type": "SALE", "is_anomaly": True
    }]

    voids = [
        {"event_id": f"RV-{random.randint(1000,9999)}", "store_id": STORE_ID,
         "register_id": register_id, "employee_id": employee_id,
         "timestamp": (base_time + timedelta(minutes=8)).strftime("%Y-%m-%d %H:%M:%S"),
         "sku": item1["sku"], "item_name": item1["name"], "amount": item1["price"],
         "event_type": "VOID", "manager_approved": "No", "is_anomaly": True},
        {"event_id": f"RV-{random.randint(1000,9999)}", "store_id": STORE_ID,
         "register_id": register_id, "employee_id": employee_id,
         "timestamp": (base_time + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
         "sku": item2["sku"], "item_name": item2["name"], "amount": item2["price"],
         "event_type": "VOID", "manager_approved": "No", "is_anomaly": True},
        {"event_id": f"RV-{random.randint(1000,9999)}", "store_id": STORE_ID,
         "register_id": register_id, "employee_id": employee_id,
         "timestamp": (base_time + timedelta(minutes=11)).strftime("%Y-%m-%d %H:%M:%S"),
         "sku": item3["sku"], "item_name": item3["name"], "amount": item3["price"],
         "event_type": "VOID", "manager_approved": "No", "is_anomaly": True},
    ]

    camera = [
        {"event_id": f"CAM-{random.randint(1000,9999)}", "store_id": STORE_ID,
         "zone": "Aisle 7", "camera_id": CAMERAS["Aisle 7"],
         "timestamp": (base_time - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
         "dwell_seconds": 487, "motion_flag": True, "person_count": 1,
         "event_type": "LOITER", "is_anomaly": True},
        {"event_id": f"CAM-{random.randint(1000,9999)}", "store_id": STORE_ID,
         "zone": "Exit", "camera_id": CAMERAS["Exit"],
         "timestamp": (base_time + timedelta(minutes=13)).strftime("%Y-%m-%d %H:%M:%S"),
         "dwell_seconds": 3, "motion_flag": True, "person_count": 1,
         "event_type": "PASS", "is_anomaly": True},
    ]

    inventory = [{
        "record_id": f"INV-{random.randint(1000,9999)}", "store_id": STORE_ID,
        "sku": item1["sku"], "item_name": item1["name"], "zone": item1["zone"],
        "expected_qty": 12, "actual_qty": 9, "delta": -3,
        "timestamp": (base_time + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
        "adjusted_by": "SYSTEM", "is_anomaly": True
    }]

    return txns, voids, camera, inventory

if __name__ == "__main__":
    all_txns, all_voids, all_camera, all_inventory = [], [], [], []

    for day in range(NUM_DAYS):
        day_start = START_DATE + timedelta(days=day, hours=9)
        day_end   = START_DATE + timedelta(days=day, hours=21)

        all_txns.extend(generate_normal_transactions(day_start, day_end))
        all_voids.extend(generate_normal_voids(day_start, day_end))
        all_camera.extend(generate_normal_camera(day_start, day_end))
        all_inventory.extend(generate_normal_inventory(day_start + timedelta(hours=4)))
        all_inventory.extend(generate_normal_inventory(day_start + timedelta(hours=10)))

        # Plant sweethearting on day 3 and day 6
        if day in [2, 5]:
            t, v, c, i = plant_sweethearting(
                base_time=day_start + timedelta(hours=random.randint(1, 8)),
                employee_id=random.choice(EMPLOYEES[:5]),
                register_id=random.choice(REGISTERS)
            )
            all_txns.extend(t); all_voids.extend(v)
            all_camera.extend(c); all_inventory.extend(i)

    os.makedirs("data", exist_ok=True)
    pd.DataFrame(all_txns).sort_values("timestamp").to_csv("data/transactions.csv", index=False)
    pd.DataFrame(all_voids).sort_values("timestamp").to_csv("data/returns_voids.csv", index=False)
    pd.DataFrame(all_camera).sort_values("timestamp").to_csv("data/camera_metadata.csv", index=False)
    pd.DataFrame(all_inventory).sort_values("timestamp").to_csv("data/inventory.csv", index=False)

    print("✅ Data generated!")
    print(f"   Transactions : {len(all_txns)}")
    print(f"   Voids        : {len(all_voids)}")
    print(f"   Camera events: {len(all_camera)}")
    print(f"   Inventory    : {len(all_inventory)}")
    print(f"\n🚨 Planted 2 sweethearting scenarios (day 3 + day 6)")