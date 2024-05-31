import pandas as pd
import streamlit as st
import os
import requests
import base64
from datetime import datetime

# Set page configuration for wide layout
st.set_page_config(layout="wide")

# Define file paths for each store's inventory data
file_paths = ['files/Concord', 'files/Winston', 'files/Lake', 'files/Hickory']

# Define ext_mapping dictionary
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

mdl_mapping = {
    'ALTIMA': 'ALT',
    'ARMADA': 'ARM',
    'FRONTIER': '720',
    'KICKS': 'KIX',
    'LEAF ELECTRIC': 'LEF',
    'MURANO': 'MUR',
    'PATHFINDER': 'PTH',
    'ROGUE': 'RGE',
    'SENTRA': 'SEN',
    'TITAN': 'TTN',
    'VERSA': 'VSD',
    'Z NISMO': 'Z',
    'Z PROTO': 'Z'
}

# Function to load data and handle columns dynamically
@st.cache_data
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

# Load data from specified file paths
data_frames = load_data(file_paths)

# Combine data from all stores into a single DataFrame
if data_frames:
    combined_data = pd.concat([df[0] for df in data_frames], ignore_index=True)
    combined_data.reset_index(drop=True, inplace=True)
else:
    combined_data = pd.DataFrame()

# Load Current Inventory data from Excel file
@st.cache_data
def load_current_data(file_path):
    if os.path.exists(file_path):
        df = pd.read_excel(file_path, header=4, usecols='B:O')
        del df['Deal \nNo.']
        del df['Make']
        df.columns = [
            'STOCK', 'YEAR', 'MDL', 'MCODE', 'COLOR', 'LOT', 'COMPANY', 'AGE', 
            'STATUS', 'VIN', 'BALANCE', 'CUSTOM'
        ]
        df['YEAR'] = df['YEAR'].astype(str).str.replace(',', '')
        df['COLOR'] = df['COLOR'].apply(lambda x: ext_mapping.get(x[:3], x))
        df['MCODE'] = df['MCODE'].astype(str).str.replace(',', '')
        df['MDL'] = df['MDL'].replace(mdl_mapping)
        df.sort_values(by='COMPANY', inplace=True)
        df.reset_index(drop=True, inplace=True)
        df.fillna('', inplace=True)
        return df
    else:
        st.error(f"File {file_path} not found.")
        return pd.DataFrame()

current_data = load_current_data('InventoryUpdate.xlsx')

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

# Create tabs for "All Stores" and "Current"
tab1, tab2, tab3 = st.tabs(["All Stores", "Current", "Dealer Trade"])

# Function to save edited data back to GitHub
def save_to_github(file_path, data_frame, token):
    html_data = base64.b64encode(data_frame.to_html(index=False).encode('utf-8')).decode('utf-8')
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }
    url = f"https://api.github.com/repos/cobbtrades/Inventory/contents/{file_path}"
    
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
@st.cache_data
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

# Display combined data for all stores with filters
if not combined_data.empty:
    with tab1:
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            st.markdown(f"### All Stores Inventory")
        with cols[1]:
            model = st.selectbox('Model', options=['All'] + combined_data['MDL'].unique().tolist(), key='all_model')
        with cols[2]:
            # Filter options based on selected model
            trims = ['All'] if model == 'All' else ['All'] + combined_data[combined_data['MDL'] == model]['TRIM'].unique().tolist()
            trim = st.selectbox('Trim', options=trims, key='all_trim')
        with cols[3]:
            packages = ['All'] if model == 'All' else ['All'] + combined_data[combined_data['MDL'] == model]['PACKAGE'].unique().tolist()
            package = st.selectbox('Package', options=packages, key='all_package')
        with cols[4]:
            colors = ['All'] if model == 'All' else ['All'] + combined_data[combined_data['MDL'] == model]['EXT'].unique().tolist()
            color = st.selectbox('Color', options=colors, key='all_color')

        filtered_df = filter_data(combined_data, model, trim, package, color)
        
        num_rows = len(filtered_df)
        st.markdown(f"<span style='font-size: small;'>{num_rows} vehicles</span>", unsafe_allow_html=True)
        
        edited_df = st.data_editor(filtered_df, use_container_width=True, height=780, hide_index=True, key='all_data_editor')
        
        # Update the original dataframe with the changes from the edited dataframe
        for index, row in edited_df.iterrows():
            original_index = combined_data[combined_data['VIN'] == row['VIN']].index[0]
            combined_data.loc[original_index] = row
        
        token = os.getenv('GITHUB_TOKEN')
        if token:
            save_to_github('combined_inventory.html', combined_data, token)
else:
    st.error("No data to display.")

# Display Current Inventory data in the Current tab
with tab2:
    st.markdown("### Current CDK Inventory")
    if not current_data.empty:
        st.data_editor(current_data, use_container_width=True, height=780, hide_index=True)
    else:
        st.error("No current inventory data to display.")

st.markdown("""
    <style>
    .short-input input {
        max-width: 200px;
        margin-bottom: 0px !important;
    }
    .form-spacing {
        margin-top: -10px;
    }
    .small-spacing {
        margin-top: -10px;
    }
    .form-container {
        max-width: 600px;
        margin: auto;
    }
    .form-container .stTextInput, .form-container .stNumberInput, .form-container .stDateInput {
        max-width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

with tab3:
    st.markdown("### Dealer Trade")
    with st.form(key="dealer_trade_form"):
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.date_input("Date", value=datetime.today(), key="date_input")
        with col2:
            st.text_input("Manager", key="manager_input")
        st.markdown('<div class="small-spacing"><hr></div>', unsafe_allow_html=True)
        col3, col4, col5 = st.columns([1, 1, 2])
        with col3:
            st.checkbox("Our Trade", key="our_trade_checkbox")
            st.checkbox("Sold", key="sold_checkbox")
        with col4:
            st.checkbox("Their Trade", key="their_trade_checkbox")
            st.checkbox("Floorplan", key="floorplan_checkbox")
        with col5:
            st.text("""
            PLEASE SEND MCO/CHECK TO:
            MODERN AUTOMOTIVE SUPPORT CENTER
            3901 WEST POINT BLVD.
            WINSTON-SALEM, NC 27103
            """)
        st.markdown("---")
        st.text("Intercompany DX")
        st.text_input("# of Keys", value="2", key="keys_input")
        col6, col7 = st.columns(2)
        with col6:
            st.text_input("From:", key="from_input")
        with col7:
            st.text_input("To:", key="to_input")
        col8, col9 = st.columns(2)
        with col8:
            st.text_input("Stock Number", key="stock_number_input")
            st.text_input("Year Make Model", key="year_make_model_input")
            st.text_input("Full VIN #", key="full_vin_input")
        with col9:
            st.text_input("Key Charge", value="-400", key="key_charge_input")
            st.text_input("Pack + PPM", key="pack_ppm_input")
            st.text_input("Transfer Amount", value="33,728.00", key="transfer_amount_input")
        st.markdown("---")
        st.text("Dealership Information")
        st.text_input("Dealership Name", key="dealership_name_input")
        st.text_input("Address", key="address_input")
        st.text_input("City, State ZIP Code", key="city_state_zip_input")
        st.text_input("Phone Number", key="phone_number_input")
        st.text_input("Dealer Code", key="dealer_code_input")
        st.text_input("Contact Name", key="contact_name_input")
        st.markdown("---")
        st.text("Outgoing Unit")
        st.text_input("Outgoing Stock Number", key="outgoing_stock_number_input")
        st.text_input("Outgoing Year Make Model", key="outgoing_year_make_model_input")
        st.text_input("Outgoing Full VIN #", key="outgoing_full_vin_input")
        st.text_input("Outgoing Sale Price", key="outgoing_sale_price_input")
        st.markdown("---")
        st.text("Incoming Unit")
        st.text_input("Incoming Year Make Model", key="incoming_year_make_model_input")
        st.text_input("Incoming Full VIN #", key="incoming_full_vin_input")
        st.text_input("Incoming Purchase Price", key="incoming_purchase_price_input")
        st.markdown("---")
        st.text("Notes")
        st.text_area("", key="notes_input")
        if st.form_submit_button("Submit Trade"):
            st.success("Trade Submitted")
        st.markdown('</div>', unsafe_allow_html=True)
