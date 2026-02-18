import pandas as pd
import os

# 1. Load Data (Global Cache)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../../data")

print("⏳ Loading Network Data...")
try:
    # CDR data is heavy (100k rows), so we load it once.
    CDR_DF = pd.read_csv(os.path.join(DATA_DIR, "cdr_sample.csv"))
    print("✅ Network Data Loaded Successfully.")
except Exception as e:
    print(f"❌ Error loading Network data: {e}")
    CDR_DF = pd.DataFrame()

def check_tower_status(location_keyword: str) -> str:
    """
    Checks the status of cell towers matching a location keyword (e.g., 'Mumbai', 'Delhi').
    Returns traffic load and congestion status.
    """
    # 1. Find matching cells in the 'cell_id' column
    # We look for rows where cell_id contains the keyword (case-insensitive)
    matches = CDR_DF[CDR_DF['cell_id'].str.contains(location_keyword, case=False, na=False)]
    
    if matches.empty:
        return f"No cell towers found for location '{location_keyword}'."
    
    # 2. Analyze the busiest cell in that area
    top_cell = matches['cell_id'].value_counts().idxmax()
    session_count = matches['cell_id'].value_counts().max()
    
    # 3. Determine Congestion (Simple Logic)
    # In our dummy data, 'Hot' cells have lots of rows.
    status = "HEALTHY"
    action = "None"
    
    if session_count > 200: # Threshold for demo
        status = "CRITICAL CONGESTION"
        action = "Initiate Load Balancing -> Offload to backup frequency"
    elif session_count > 50:
        status = "MODERATE LOAD"
        action = "Monitor Closely"
        
    return f"""
    Network Status for '{location_keyword}':
    - Primary Tower: {top_cell}
    - Active Sessions: {session_count}
    - Status: {status}
    - Recommended Action: {action}
    """