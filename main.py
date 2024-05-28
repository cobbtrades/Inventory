import pandas as pd
import streamlit as st
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

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
        'ORD_CUST_DATE': 'ORD_DATE', 'DLR_DLV_DT': 'DLV_DATE'
    }
    ext_mapping = {
        'A20': 'RED ALERT', 'B51': 'ELECTRIC BLUE', 'BW5': 'HERMOSA BLUE', 'CAS': 'MOCHA ALMOND',
        'DAN': 'OBSIDIAN GREEN', 'DAQ': 'TACTICAL GREEN', 'EBB': 'MONARCH ORANGE', 'EBL': 'SUNSET DRIFT',
        'G41': 'MAGNETIC BLACK', 'GAQ': 'GRAY/BLACK ROOF', 'HAL': 'BAJA STORM', 'K23': 'BRILLIANT SILVER',
        'KAD': 'GUN METALLIC', 'KAY': 'CHAMPAGNE SILVER', 'KBY': 'BOULDER GRAY', 'KCH': 'ETHOS GRAY',
        'KH3': 'SUPER BLACK', 'NAW': 'COULIS RED', 'NBL': 'SCARLET EMBER', 'NBQ': 'ROSEWOOD',
        'NBY': 'CARDINAL RED', 'QAB': 'PEARL WHITE', 'QAC': 'ASPEN WHITE', 'QAK': 'GLACIER WHITE',
        'QM1': 'FRESH POWDER', 'RAY': 'DEEP BLUE PEARL', 'RBD': 'STORM BLUE', 'RBY': 'CASPIAN BLUE',
        'RCJ': 'DEEP OCEAN BLUE', 'XAB': 'WHITE/BLACK', 'XAH': 'ORANGE/BLACK', 'XBJ': 'WHITE/BLACK',
        'XDU': 'RED/BLACK', 'XEU': 'BLUE/BLACK', 'XEW': 'CHAMP/BLACK', 'XEX': 'GRAY/BLACK',
        'XFN': 'GREEN/BLACK', 'XGY': 'BLUE/BLACK', 'XKV': 'TAN/BLACK', 'XEV': 'ORANGE/BLACK',
        'DAP': 'NORTHERN LIGHTS', 'GAT': 'BLACK DIAMOND', 'XGA': 'WHITE/BLACK', 'XGB': 'SILVER/BLACK',
        'XGD': 'RED/BLACK', 'XGH': 'GRAY/BLACK', 'XGJ': 'COPPER/BLACK', 'XGU': 'BLUE/BLACK',
        'NCA': 'BURGUNDY', 'QBE': 'EVEREST WHITE', 'KBZ': 'ATLANTIC GRAY', 'XKY': 'ATLANTIC/BLACK ROOF',
        'XKJ': 'EVEREST/BLACK', 'RCF': 'BLUESTONE PEARL', 'XHQ': 'DEEP OCEAN/BLACK', 'XJR': 'SEIRAN BLUE/BLACK'
    }
    data_frames = []
    
    for file in file_paths:
        if os.path.exists(file):
            dfs = pd.read_html(file)
            if dfs:
                df = dfs[0]
                df = df[[col for col in expected_columns if col in df.columns]]
                df.rename(columns=new_column_names, inplace=True)
                if 'MDLYR' in df.columns:
                    df['MDLYR'] = df['MDLYR'].apply(lambda x: str(x).strip()[:-1])
                if 'MCODE' in df.columns:
                    df['MCODE'] = df['MCODE'].astype(str).str.replace(',', '')
                if 'MDL' in df.columns:
                    df['EXT'] = df['EXT'].replace(ext_mapping)
                date_columns = ['ETA', 'DLV_DATE', 'ORD_DATE']
                df[date_columns] = df[date_columns].apply(lambda col: pd.to_datetime(col).dt.strftime('%m-%d-%Y'))
                df['Premium'] = df['GOPTS'].apply(lambda x: 'PRM' if any(sub in x for sub in ['PRM', 'PR1', 'PR2', 'PR3']) else '')
                df['Technology'] = df['GOPTS'].apply(lambda x: 'TECH' if any(sub in x for sub in ['TEC', 'TE1', 'TE2', 'TE3']) else '')
                df['Convenience'] = df['GOPTS'].apply(lambda x: 'CONV' if any(sub in x for sub in ['CN1', 'CN2', 'CN3', 'CN4', 'CN5']) else '')
                df['PACKAGE'] = df[['Premium', 'Technology', 'Convenience']].apply(lambda x: ' '.join(filter(None, x)), axis=1)
                df.drop(columns=['Premium', 'Technology', 'Convenience', 'GOPTS'], inplace=True)
                cols = df.columns.tolist()
                drive_index = cols.index('DRIVE')
                cols.insert(drive_index + 1, cols.pop(cols.index('PACKAGE')))
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

# Function to filter data based on selectbox inputs
def filter_data(df, model, trim, package, color):
    if model != 'All':
        df = df[df['MDL'] == model]
    if trim != 'All':
        df = df[df['TRIM'] == trim]
    if package != 'All':
        df = df[df['PACKAGE'].str.contains(package)]
    if color != 'All':
        df = df[df['EXT'] == color]
    return df

# Function to display data for each store
def display_store_data(tab, df, file_path, store_name, tab_key):
    with tab:
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            st.markdown(f"### {store_name} Inventory")
        with cols[1]:
            model = st.selectbox('Model', options=['All'] + df['MDL'].unique().tolist(), key=f'{tab_key}_model')
        with cols[2]:
            # Filter options based on selected model
            trims = ['All'] if model == 'All' else ['All'] + df[df['MDL'] == model]['TRIM'].unique().tolist()
            trim = st.selectbox('Trim', options=trims, key=f'{tab_key}_trim')
        with cols[3]:
            packages = ['All'] if model == 'All' else ['All'] + df[df['MDL'] == model]['PACKAGE'].unique().tolist()
            package = st.selectbox('Package', options=packages, key=f'{tab_key}_package')
        with cols[4]:
            colors = ['All'] if model == 'All' else ['All'] + df[df['MDL'] == model]['EXT'].unique().tolist()
            color = st.selectbox('Color', options=colors, key=f'{tab_key}_color')

        filtered_df = filter_data(df, model, trim, package, color)
        
        num_rows = len(filtered_df)
        st.markdown(f"<span style='font-size: small;'>{num_rows} vehicles</span>", unsafe_allow_html=True)
        
        edited_df = st.data_editor(filtered_df, height=780, hide_index=True, key=f'{tab_key}_data_editor')
        
        # Update the original dataframe with the changes from the edited dataframe
        for index, row in edited_df.iterrows():
            original_index = df[df['VIN'] == row['VIN']].index[0]
            df.loc[original_index] = row
        
        token = os.getenv('GITHUB_TOKEN')
        if token:
            save_to_github(file_path, df, token)

def authenticate(username, password):
    valid_username = os.getenv('VALID_USERNAME')
    valid_password = os.getenv('VALID_PASSWORD')
    st.write(f"DEBUG: Valid Username: {valid_username}, Valid Password: {valid_password}")  # Debugging line
    return username == valid_username and password == valid_password

# Login form
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.write("Please login to access the inventory data")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.success("Login successful")
            else:
                st.error("Invalid username or password")
                
if st.session_state.authenticated:
    # Display individual store data
    store_names = ["Concord", "Winston", "Lake", "Hickory"]
    tabs = [tab1, tab2, tab3, tab4]
    if data_frames:
        for i, (df, file_path) in enumerate(data_frames):
            display_store_data(tabs[i], df, file_path, store_names[i], f'store_{i}')
    
    # Display combined data for all stores
    if not combined_data.empty:
        num_rows = len(combined_data)
        with tab5:
            st.markdown(f"### Group Inventory <span style='font-size: small;'>{num_rows} vehicles</span>", unsafe_allow_html=True)
            st.data_editor(combined_data, use_container_width=True, height=780, hide_index=True)
    else:
        st.error("No data to display.")
