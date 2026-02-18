import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid

# Configuration
NUM_USERS = 5000       # Total unique subscribers
NUM_RECORDS = 100000   # Rows per file (approx)
START_DATE = datetime(2024, 1, 1)

print("🚀 Initializing Dummy Data Generator...")

# --- 1. Generate Base Users (UDR) ---
# We create a mix of "Premium" and "Standard" users to test personalization.
print(f"Generating {NUM_USERS} unique users...")

msisdns = [f"91{random.randint(7000000000, 9999999999)}" for _ in range(NUM_USERS)]
plans = ["Basic_4G", "Super_Streamer_5G", "Gold_Family", "Pay_As_You_Go"]
device_types = ["iPhone 15", "Samsung S24", "OnePlus 11", "Xiaomi Redmi Note"]

udr_data = []
for ms in msisdns:
    plan = random.choice(plans)
    is_premium = "5G" in plan or "Gold" in plan
    udr_data.append({
        "msisdn": ms,
        "imsi": f"404{random.randint(1000000000, 9999999999)}",
        "plan_name": plan,
        "monthly_quota_gb": 100 if is_premium else 30,
        "default_5qi": 5 if is_premium else 9,
        "is_premium": is_premium,
        "device_type": random.choice(device_types),
        "priority_arp": 1 if is_premium else 5,  # Lower is better priority
        "roaming_allowed": random.choice([True, False])
    })

df_udr = pd.DataFrame(udr_data)
df_udr.to_csv("udr_sample.csv", index=False)
print("✅ UDR Generated (User Profiles)")


# --- 2. Generate Network Traffic (CDR) ---
# We simulate "Hot Cells" by forcing 40% of traffic into just 5 Cell IDs.
print(f"Generating {NUM_RECORDS} CDR records...")

hot_cells = ["CELL_001_MUMBAI", "CELL_002_DELHI", "CELL_003_BANGALORE"]
normal_cells = [f"CELL_{i:03d}_GENERIC" for i in range(10, 100)]

cdr_data = []
for _ in range(NUM_RECORDS):
    # FIXED PROBABILITIES:
    # 18 hours of "low traffic" (2% each) = 36%
    # 6 hours of "peak traffic" (varied) = 64%
    # Total = 100%
    hour = np.random.choice(range(24), p=[0.02]*18 + [0.11, 0.13, 0.13, 0.11, 0.10, 0.06]) 
    
    minute = random.randint(0, 59)
    ts = START_DATE + timedelta(days=random.randint(0, 7), hours=int(hour), minutes=minute)
    
    # 30% chance user is in a "Hot Cell" (Simulating congestion)
    cell = random.choice(hot_cells) if random.random() < 0.3 else random.choice(normal_cells)
    
    cdr_data.append({
        "record_id": uuid.uuid4().hex[:12],
        "msisdn": random.choice(msisdns),
        "start_time": ts,
        "duration_sec": random.randint(10, 3600),
        "cell_id": cell,
        "rat": "5G" if "5G" in cell else "4G",
        "bytes_downlink": random.randint(1_000, 1_000_000_000), # Up to 1GB
        "bytes_uplink": random.randint(1_000, 50_000_000),
        "qos_5qi": random.choice([5, 6, 9]),
        "result_code": 2001 # Success
    })

df_cdr = pd.DataFrame(cdr_data)
df_cdr.to_csv("cdr_sample.csv", index=False)
print("✅ CDR Generated (Network Calls/Sessions)")


# --- 3. Generate App Usage (IPDR) ---
# Focus on "Video Streaming" to trigger the QoE Agent.
print(f"Generating {NUM_RECORDS} IPDR records...")

apps = ["Netflix", "YouTube", "Instagram", "WhatsApp", "Zoom", "WebBrowsing"]
weights = [0.3, 0.3, 0.2, 0.1, 0.05, 0.05] # High video usage

ipdr_data = []
for _ in range(NUM_RECORDS):
    app = np.random.choice(apps, p=weights)
    ms = random.choice(msisdns)
    
    # If it's video, make it heavy data
    if app in ["Netflix", "YouTube"]:
        downlink = random.randint(50_000_000, 2_000_000_000) # 50MB to 2GB
    else:
        downlink = random.randint(1_000, 10_000_000)

    ipdr_data.append({
        "record_id": uuid.uuid4().hex[:12],
        "msisdn": ms,
        "app_category": app,
        "protocol": "UDP" if app in ["Zoom", "YouTube"] else "TCP",
        "bytes_downlink": downlink,
        "flow_duration_sec": random.randint(30, 7200),
        "dst_port": 443
    })

df_ipdr = pd.DataFrame(ipdr_data)
df_ipdr.to_csv("ipdr_sample.csv", index=False)
print("✅ IPDR Generated (App Usage)")


# --- 4. Generate Billing Events (EDR) ---
# To show "Top-ups" or "Purchases"
print(f"Generating {int(NUM_RECORDS/5)} EDR records...")

edr_data = []
for _ in range(int(NUM_RECORDS/5)): # Fewer billing events than traffic
    edr_data.append({
        "record_id": uuid.uuid4().hex[:12],
        "msisdn": random.choice(msisdns),
        "event_time": START_DATE + timedelta(days=random.randint(0, 7)),
        "event_type": random.choice(["Recharge", "Booster_Pack", "VAS_Activation"]),
        "charge_amount_inr": random.choice([19, 29, 99, 499, 999]),
        "success": True
    })

df_edr = pd.DataFrame(edr_data)
df_edr.to_csv("edr_sample.csv", index=False)
print("✅ EDR Generated (Billing)")

print("\n🎉 All 4 files created successfully!")