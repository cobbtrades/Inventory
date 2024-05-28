import pandas as pd
import streamlit as st
import os
import requests
import base64

# Set page configuration
st.set_page_config(layout="wide")

# Define file paths
file_paths = ['files/Concord', 'files/Winston', 'files/Lake', 'files/Hickory']

# Function to load data and handle columns dynamically
def load_data(file_paths):
    expected_columns = [
        'LOC_DESC', 'DLRORD', 'MDLYR', 'MDL', 'TRM_LVL', 'DRV_TRN', 'EXT', 'INT',
        'MCODE', 'VIN', 'DEALER_NAME', 'DLR_DLV_DT', 'DLRETA', 'ORD_CUST_NAME',
        'ORD_CUST_EMAIL_ADDR', 'ORD_CUST_DATE', 'GOPTS'
    ]
    new_column_names = {
        'LOC_DESC': 'LOC', 'DLRORD': 'ORDER', 'TRM_LVL': 'TRIM', 'DRV_TRN': 'DRIVE',
        'DLRETA': 'ETA', 'ORD_CUST_NAME': 'CUST_NAME', 'ORD_CUST_EMAIL_ADDR': 'CUST_EMAIL',
        'ORD_CUST_DATE': 'ORD_DATE', 'DLR_DLV_DT': 'DLV_DATE', 'EXT': 'COLOR'
    }
    ext_mapping = {
        'A20': 'Red Alert', 'B51': 'Electric Blue', 'BW5': 'Hermosa Blue', 'CAS': 'Mocha Almond',
        'DAN': 'Obsidian Green', 'DAQ': 'Tactical Green', 'EBB': 'Monarch Orange', 'EBL': 'Sunset Drift',
        'G41': 'Magnetic Black', 'GAQ': 'Gray/Black Roof', 'HAL': 'Baja Storm', 'K23': 'Brilliant Silver',
        'KAD': 'Gun Metallic', 'KAY': 'Champagne Silver', 'KBY': 'Boulder Gray', 'KCH': 'Ethos Gray',
        'KH3': 'Super Black', 'NAW': 'Coulis Red', 'NBL': 'Scarlet Ember', 'NBQ': 'Rosewood',
        'NBY': 'Cardinal Red', 'QAB': 'Pearl White', 'QAC': 'Aspen White', 'QAK': 'Glacier White',
        'QM1': 'Fresh Powder', 'RAY': 'Deep Blue Pearl', 'RBD': 'Storm Blue', 'RBY': 'Caspian Blue',
        'RCJ': 'Deep Ocean Blue', 'XAB': 'White/Black', 'XAH': 'Orange/Black', 'XBJ': 'White/Black',
        'XDU': 'Red/Black', 'XEU': 'Blue/Black', 'XEW': 'Champ/Black', 'XEX': 'Gray/Black',
        'XFN': 'Green/Black', 'XGY': 'Blue/Black', 'XKV': 'Tan/Black', 'XEV': 'Orange/Black',
        'DAP': 'Northern Lights', 'GAT': 'Black Diamond', 'XGA': 'White/Black', 'XGB': 'Silver/Black',
        'XGD': 'Red/Black', 'XGH': 'Gray/Black', 'XGJ': 'Copper/Black', 'XGU': 'Blue/Black',
        'NCA': 'Burgundy', 'QBE': 'Everest White', 'KBZ': 'Atlantic Gray', 'XKY': 'Atlantic/Black Roof',
        'XKJ': 'Everest/Black', 'RCF': 'Bluestone Pearl', 'XHQ': 'Deep Ocean/Black', 'XJR': 'Seiran Blue/Black'
    }
    data_frames = []
    
    for file in file_paths:
        if os.path.exists(file):
            dfs = pd.read_html(file)
            if dfs:
                df = dfs[0]
                df = df[[col for col in expected_columns if col in df.columns]]
                df.rename(columns=new_column_names, inplace=True)
                df['MDLYR'] = df['MDLYR'].apply(lambda x: str(x).strip()[:-1])
                df['MCODE'] = df['MCODE'].astype(str).str.replace(',', '')
                df['COLOR'] = df['COLOR'].replace(ext_mapping)
                date_columns = ['ETA', 'DLV_DATE', 'ORD_DATE']
                df[date_columns] = df[date_columns].apply(lambda col: pd.to_datetime(col).dt.strftime('%m-%d-%Y'))
                df['Premium'] = df['GOPTS'].apply(lambda x: 'PRM' if any(sub in x for sub in ['PRM', 'PR1', 'PR2', 'PR3']) else '')
                df['Technology'] = df['GOPTS'].apply(lambda x: 'TECH' if any(sub in x for sub in ['TEC', 'TE1', 'TE2', 'TE3']) else '')
                df['Convenience'] = df['GOPTS'].apply(lambda x: 'CONV' if any(sub in x for sub in ['CN1', 'CN2', 'CN3', 'CN4', 'CN5']) else '')
                df['PACKAGE'] = df[['Premium', 'Technology', 'Convenience']].apply(lambda x: ' '.join(filter(None, x)), axis=1)
                df.drop(columns=['Premium', 'Technology', 'Convenience', 'GOPTS'], inplace=True)
                cols = df.columns.tolist()
                drive_index = cols.index('DRIVE')
                cols.insert(drive_index + 1, cols.pop(cols.index('Package')))
                df = df[cols]
                df.sort_values(by='MDL', inplace=True)
                df.reset_index(drop=True, inplace=True)
                df.fillna('', inplace=True)
                data_frames.append((df, file))
        else:
            st.error(f"File {file} not found in the repository.")
    return data_frames

# Load data
data_frames = load_data(file_paths)

# Combine data
if data_frames:
    combined_data = pd.concat([df[0] for df in data_frames], ignore_index=True)
    combined_data.reset_index(drop=True, inplace=True)
else:
    combined_data = pd.DataFrame()

# Custom CSS for padding and container width
st.write(
    """
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Concord", "Winston", "Lake", "Hickory", "All Stores"])

# Function to save edited data back to GitHub
def save_to_github(file_path, data_frame, token):
    html_data = base64.b64encode(data_frame.to_html(index=False).encode('utf-8')).decode('utf-8')
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }
    path = file_path
    url = f"https://api.github.com/repos/cobbtrades/Inventory/contents/{path}"
    
    # Get the SHA of the file to update
    response = requests.get(url, headers=headers)
    response_data = response.json()
    sha = response_data.get("sha")

    # Prepare the payload
    payload = {
        "message": "Update data",
        "content": html_data,
        "sha": sha
    }
    
    # Update the file on GitHub
    update_response = requests.put(url, headers=headers, json=payload)
    if update_response.status_code == 200:
        st.success(f"Successfully updated {file_path} on GitHub.")
    else:
        st.error(f"Failed to update {file_path} on GitHub: {update_response.text}")

# Function to display data for each store
def display_store_data(tab, df, file_path, store_name):
    with tab:
        num_rows = len(df)
        st.markdown(f"### {store_name} Inventory <span style='font-size: small;'>{num_rows} vehicles</span>", unsafe_allow_html=True)
        edited_df = st.data_editor(df, height=780, hide_index=True)
        token = os.getenv('GITHUB_TOKEN')
        if token and not edited_df.equals(df):
            save_to_github(file_path, edited_df, token)

# Display individual store data
store_names = ["Concord", "Winston", "Lake", "Hickory"]
tabs = [tab1, tab2, tab3, tab4]
if data_frames:
    for i, (df, file_path) in enumerate(data_frames):
        display_store_data(tabs[i], df, file_path, store_names[i])

# Display combined data for all stores
if not combined_data.empty:
    num_rows = len(combined_data)
    with tab5:
        st.markdown(f"### Group Inventory <span style='font-size: small;'>{num_rows} vehicles</span>", unsafe_allow_html=True)
        st.data_editor(combined_data, use_container_width=True, height=780, hide_index=True)
else:
    st.error("No data to display.")
