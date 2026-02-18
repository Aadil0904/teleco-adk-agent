import pandas as pd
import os
from datetime import datetime

# 1. Load Data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../../data")

print("⏳ Loading QoE Data...")
try:
    UDR_DF = pd.read_csv(os.path.join(DATA_DIR, "udr_sample.csv"))
    IPDR_DF = pd.read_csv(os.path.join(DATA_DIR, "ipdr_sample.csv"))
    print("✅ QoE Data Loaded.")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    UDR_DF = pd.DataFrame()
    IPDR_DF = pd.DataFrame()

def check_user_profile(msisdn: str) -> dict:
    user = UDR_DF[UDR_DF['msisdn'].astype(str) == str(msisdn)]
    if user.empty: return {}
    return user.iloc[0].to_dict()

def analyze_streaming_usage(msisdn: str) -> str:
    """
    Returns a rich 'User Persona' string including habits, device, and spending power.
    """
    # 1. Get Profile
    user_profile = check_user_profile(msisdn)
    if not user_profile: return f"User {msisdn} not found."

    plan_name = user_profile.get('plan_name', 'Unknown')
    device = user_profile.get('device_type', 'Unknown Device')
    quota_limit = user_profile.get('monthly_quota_gb', 0)

    # 2. Filter IPDR for Video
    user_logs = IPDR_DF[
        (IPDR_DF['msisdn'].astype(str) == str(msisdn)) & 
        (IPDR_DF['app_category'].isin(['Netflix', 'YouTube', 'Prime', 'Disney+']))
    ].copy()
    
    if user_logs.empty:
        return f"User {msisdn} has minimal video usage."

    # 3. Calculate "Flavor" Stats
    total_gb = round(user_logs['bytes_downlink'].sum() / (1024**3), 2)
    quota_used_percent = round((total_gb / quota_limit) * 100, 1)
    
    # top_app = user_logs['app_category'].mode()[0] # The app they use most
    # (Since dummy data is random, we just grab the most frequent one)
    top_app = user_logs['app_category'].value_counts().idxmax()

    # 4. Infer "Time of Day" Persona (Mock logic since we didn't parse full dates in global load)
    # We use the random record_id or hash to deterministically assign a "Habit" for the demo
    # This ensures the same user always gets the same "Time" persona.
    user_hash = hash(msisdn) % 3
    if user_hash == 0:
        habit = "Late Night Binger (10 PM - 2 AM)"
    elif user_hash == 1:
        habit = "Evening Commuter (6 PM - 8 PM)"
    else:
        habit = "Weekend Warrior (Heavy Sunday usage)"

    # 5. Construct the "Rich Context" for LLM
    return f"""
    User Persona Report for {msisdn}:
    -----------------------------------
    - Device: {device} (High-end devices suggest higher willingness to pay).
    - Current Plan: {plan_name}
    - Data Health: {quota_used_percent}% used.
    
    - Streaming Habit: {habit}
    - Favorite App: {top_app}
    - Total Consumption: {total_gb} GB
    
    (Technical Note: If they stream at night, suggest 'Night Boosters'. If they commute, suggest 'Mobility Passes'.)
    """

def scan_for_risky_users(limit=20):
    # (Same as before)
    video_traffic = IPDR_DF[IPDR_DF['app_category'].isin(['Netflix', 'YouTube'])]
    if video_traffic.empty: return []
    usage = video_traffic.groupby('msisdn')['bytes_downlink'].sum()
    return (usage / (1024**3)).sort_values(ascending=False).head(limit)