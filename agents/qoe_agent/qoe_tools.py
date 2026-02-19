import pandas as pd
import os

# 1. Load All Data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../../data")

print("⏳ Loading Complete Telecom Data (UDR, IPDR, CDR, EDR)...")
try:
    UDR_DF = pd.read_csv(os.path.join(DATA_DIR, "udr_sample.csv"))
    IPDR_DF = pd.read_csv(os.path.join(DATA_DIR, "ipdr_sample.csv"))
    CDR_DF = pd.read_csv(os.path.join(DATA_DIR, "cdr_sample.csv"))
    EDR_DF = pd.read_csv(os.path.join(DATA_DIR, "edr_sample.csv"))
    print("✅ All Data Loaded.")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    UDR_DF, IPDR_DF, CDR_DF, EDR_DF = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def scan_all_risks(limit=20):
    """
    Scans the entire database and calculates the 4 risk pillars for each user.
    """
    if UDR_DF.empty: return []

    # 1. Base Users & Quota Limits
    users = UDR_DF[['msisdn', 'plan_name', 'monthly_quota_gb', 'is_premium']].copy()
    users['msisdn'] = users['msisdn'].astype(str)

    # 2. Stream Risk (Video bytes from IPDR)
    video_df = IPDR_DF[IPDR_DF['app_category'].isin(['Netflix', 'YouTube'])]
    stream_usage = video_df.groupby('msisdn')['bytes_downlink'].sum() / (1024**3)
    stream_usage = stream_usage.reset_index(name='video_gb')
    stream_usage['msisdn'] = stream_usage['msisdn'].astype(str)

    # 3. Voice Risk (Short calls / Drops from CDR)
    drops = CDR_DF[CDR_DF['duration_sec'] < 15]
    voice_drops = drops.groupby('msisdn').size().reset_index(name='dropped_calls')
    voice_drops['msisdn'] = voice_drops['msisdn'].astype(str)

    # 4. Total Usage for Quota Risk
    total_usage = IPDR_DF.groupby('msisdn')['bytes_downlink'].sum() / (1024**3)
    total_usage = total_usage.reset_index(name='total_gb')
    total_usage['msisdn'] = total_usage['msisdn'].astype(str)

    # 5. Billing Risk (EDR charges)
    charges = EDR_DF[EDR_DF['charge_amount_inr'] > 0]
    billing = charges.groupby('msisdn').size().reset_index(name='charge_events')
    billing['msisdn'] = billing['msisdn'].astype(str)

    # Merge everything together
    df = users.merge(stream_usage, on='msisdn', how='left')
    df = df.merge(voice_drops, on='msisdn', how='left')
    df = df.merge(total_usage, on='msisdn', how='left')
    df = df.merge(billing, on='msisdn', how='left')
    df.fillna(0, inplace=True)

    # Calculate Quota Percentage
    df['monthly_quota_gb'] = df['monthly_quota_gb'].replace(0, 1) # Prevent division by zero
    df['Quota_Risk_Pct'] = (df['total_gb'] / df['monthly_quota_gb']) * 100
    
    # Sort by Issue Score
    df['Issue_Score'] = df['Quota_Risk_Pct'] + (df['dropped_calls'] * 10) + (df['charge_events'] * 20)
    df = df.sort_values(by='Issue_Score', ascending=False).head(limit)

    results = []
    for _, row in df.iterrows():
        v_risk = "HIGH" if row['dropped_calls'] >= 4 else ("MEDIUM" if row['dropped_calls'] >= 2 else "LOW")
        s_risk = "HIGH" if row['video_gb'] > 15 else ("MEDIUM" if row['video_gb'] > 5 else "LOW")
        
        q_pct = row['Quota_Risk_Pct']
        q_risk = f"HIGH ({q_pct:.0f}%)" if q_pct > 90 else (f"MEDIUM ({q_pct:.0f}%)" if q_pct > 75 else f"LOW ({q_pct:.0f}%)")
        
        # --- THE FIX: Synced Billing Logic ---
        if row['is_premium'] and row['charge_events'] >= 2:
            b_risk = "SYSTEM MISMATCH"
        elif not row['is_premium'] and row['charge_events'] >= 5:
            b_risk = "HIGH OVERAGES"
        else:
            b_risk = "NONE"

        results.append({
            "MSISDN": row['msisdn'],
            "Voice": v_risk,
            "Stream": s_risk,
            "Quota": q_risk,
            "Billing": b_risk
        })
    return results

def get_comprehensive_user_context(msisdn: str) -> str:
    """
    Feeds the LLM the EXACT same labels the dashboard uses (Single Source of Truth).
    """
    user = UDR_DF[UDR_DF['msisdn'].astype(str) == str(msisdn)]
    if user.empty: return f"User {msisdn} not found."
    
    plan = user.iloc[0]['plan_name']
    premium = user.iloc[0]['is_premium']
    quota = user.iloc[0]['monthly_quota_gb']
    
    # Raw Stats
    drops = len(CDR_DF[(CDR_DF['msisdn'].astype(str) == str(msisdn)) & (CDR_DF['duration_sec'] < 15)])
    video_gb = IPDR_DF[(IPDR_DF['msisdn'].astype(str) == str(msisdn)) & (IPDR_DF['app_category'].isin(['Netflix', 'YouTube']))]['bytes_downlink'].sum() / (1024**3)
    total_gb = IPDR_DF[IPDR_DF['msisdn'].astype(str) == str(msisdn)]['bytes_downlink'].sum() / (1024**3)
    charges = len(EDR_DF[(EDR_DF['msisdn'].astype(str) == str(msisdn)) & (EDR_DF['charge_amount_inr'] > 0)])
    
    # Calculate exact UI Labels
    v_risk = "HIGH" if drops >= 4 else ("MEDIUM" if drops >= 2 else "LOW")
    s_risk = "HIGH" if video_gb > 15 else ("MEDIUM" if video_gb > 5 else "LOW")
    q_pct = (total_gb / quota) * 100 if quota > 0 else 0
    q_risk = f"HIGH ({q_pct:.0f}%)" if q_pct > 90 else (f"LOW ({q_pct:.0f}%)")
    
    # Precise Billing Labels
    if premium and charges >= 2:
        b_risk = "SYSTEM MISMATCH (Premium user incorrectly charged)"
    elif not premium and charges >= 5:
        b_risk = "HIGH OVERAGES (Basic user hitting pay-as-you-go fees)"
    else:
        b_risk = "NONE"

    return f"""
    Dashboard Risk Status for {msisdn}:
    - Voice Risk: {v_risk} ({drops} drops detected)
    - Stream Risk: {s_risk} ({video_gb:.2f} GB video usage)
    - Quota Risk: {q_risk}
    - Billing Issue: {b_risk}
    - Plan Context: {plan} (Premium: {premium})
    """