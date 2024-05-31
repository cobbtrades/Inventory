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
        max-width: 100px;
        margin-bottom: 0px !important;
    }
    .form-spacing {
        margin-top: -40px;
    }
    .small-spacing {
        margin-top: -40px;
    }
    .small-input-box .stTextInput > div > div > input {
        width: 50px;
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
def calculate_transfer_amount(key_charge, projected_cost):
    return projected_cost - key_charge
def format_currency(value):
    return "${:,.2f}".format(value)
    
def create_pdf(data, filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica", 12)

    c.drawString(100, height - 40, f"Date: {data['date']}")
    c.drawString(100, height - 60, f"Manager: {data['manager']}")
    c.drawString(100, height - 100, "Dealer Trade Details:")
    c.drawString(100, height - 120, f"From: {data['from']}")
    c.drawString(100, height - 140, f"To: {data['to']}")
    c.drawString(100, height - 160, f"Stock Number: {data['stock_number']}")
    c.drawString(100, height - 180, f"Year Make Model: {data['year_make_model']}")
    c.drawString(100, height - 200, f"Full VIN: {data['full_vin']}")
    c.drawString(100, height - 220, f"Key Charge: {data['key_charge']}")
    c.drawString(100, height - 240, f"Projected Cost: {data['projected_cost']}")
    c.drawString(100, height - 260, f"Transfer Amount: {data['transfer_amount']}")
    
    c.drawString(100, height - 300, "Non-Modern Dealership Information:")
    c.drawString(100, height - 320, f"Dealership Name: {data['dealership_name']}")
    c.drawString(100, height - 340, f"Address: {data['address']}")
    c.drawString(100, height - 360, f"City, State ZIP: {data['city_state_zip']}")
    c.drawString(100, height - 380, f"Phone Number: {data['phone_number']}")
    c.drawString(100, height - 400, f"Dealer Code: {data['dealer_code']}")
    c.drawString(100, height - 420, f"Contact Name: {data['contact_name']}")

    c.drawString(100, height - 460, "Outgoing Unit:")
    c.drawString(100, height - 480, f"Outgoing Stock Number: {data['outgoing_stock_number']}")
    c.drawString(100, height - 500, f"Outgoing Year Make Model: {data['outgoing_year_make_model']}")
    c.drawString(100, height - 520, f"Outgoing Full VIN: {data['outgoing_full_vin']}")
    c.drawString(100, height - 540, f"Outgoing Sale Price: {data['outgoing_sale_price']}")

    c.drawString(100, height - 580, "Incoming Unit:")
    c.drawString(100, height - 600, f"Incoming Year Make Model: {data['incoming_year_make_model']}")
    c.drawString(100, height - 620, f"Incoming Full VIN: {data['incoming_full_vin']}")
    c.drawString(100, height - 640, f"Incoming Purchase Price: {data['incoming_purchase_price']}")

    c.save()

# Function to print PDF
def print_pdf(filename):
    conn = cups.Connection()
    printers = conn.getPrinters()
    default_printer = list(printers.keys())[0]
    conn.printFile(default_printer, filename, "Trade Document", {})

# Form for Dealer Trade
with st.form(key="dealer_trade_form"):
    col1, col2 = st.columns(2)
    with col1:
        current_date = datetime.today()
        formatted_date = current_date.strftime("%B %d, %Y")
        st.write(f"Date: {formatted_date}")
    with col2:
        manager = st.text_input("Manager", key="manager_input")

    col3, col4, col5 = st.columns([1, 1, 2])
    with col3:
        our_trade = st.checkbox("Our Trade", key="our_trade_checkbox")
        sold = st.checkbox("Sold", key="sold_checkbox")
    with col4:
        their_trade = st.checkbox("Their Trade", key="their_trade_checkbox")
        floorplan = st.checkbox("Floorplan", key="floorplan_checkbox")
    with col5:
        st.text("""
        PLEASE SEND MCO/CHECK TO:
        MODERN AUTOMOTIVE SUPPORT CENTER
        3901 WEST POINT BLVD.
        WINSTON-SALEM, NC 27103
        """)
    st.text("Intercompany DX")
    col6, col7 = st.columns(2)
    with col6:
        from_location = st.text_input("From:", key="from_input")
    with col7:
        to_location = st.text_input("To:", key="to_input")

    col8, col9 = st.columns(2)
    with col8:
        stock_number = st.text_input("Stock Number", key="stock_number_input")
        year_make_model = st.text_input("Year Make Model", key="year_make_model_input")
        full_vin = st.text_input("Full VIN #", key="full_vin_input")
    with col9:
        key_charge = st.number_input("Key Charge ($)", value=0.00, format="%.2f", key="key_charge_input")
        projected_cost = st.number_input("Projected Cost ($)", value=0.00, format="%.2f", key="projected_cost_input")
        transfer_amount = calculate_transfer_amount(key_charge, projected_cost)
        formatted_transfer_amount = format_currency(transfer_amount)
        st.text_input("Transfer Amount", value=formatted_transfer_amount, key="transfer_amount_input", disabled=True)

    st.text("Non-Modern Dealership Information")
    dealership_name = st.text_input("Dealership Name", key="dealership_name_input")
    address = st.text_input("Address", key="address_input")
    city_state_zip = st.text_input("City, State ZIP Code", key="city_state_zip_input")
    phone_number = st.text_input("Phone Number", key="phone_number_input")
    dealer_code = st.text_input("Dealer Code", key="dealer_code_input")
    contact_name = st.text_input("Contact Name", key="contact_name_input")

    st.text("Outgoing Unit")
    outgoing_stock_number = st.text_input("Outgoing Stock Number", key="outgoing_stock_number_input")
    outgoing_year_make_model = st.text_input("Outgoing Year Make Model", key="outgoing_year_make_model_input")
    outgoing_full_vin = st.text_input("Outgoing Full VIN #", key="outgoing_full_vin_input")
    outgoing_sale_price = st.text_input("Outgoing Sale Price", key="outgoing_sale_price_input")

    st.text("Incoming Unit")
    incoming_year_make_model = st.text_input("Incoming Year Make Model", key="incoming_year_make_model_input")
    incoming_full_vin = st.text_input("Incoming Full VIN #", key="incoming_full_vin_input")
    incoming_purchase_price = st.text_input("Incoming Purchase Price", key="incoming_purchase_price_input")

    if st.form_submit_button("Submit Trade"):
        data = {
            'date': formatted_date,
            'manager': manager,
            'our_trade': our_trade,
            'sold': sold,
            'their_trade': their_trade,
            'floorplan': floorplan,
            'from': from_location,
            'to': to_location,
            'stock_number': stock_number,
            'year_make_model': year_make_model,
            'full_vin': full_vin,
            'key_charge': key_charge,
            'projected_cost': projected_cost,
            'transfer_amount': formatted_transfer_amount,
            'dealership_name': dealership_name,
            'address': address,
            'city_state_zip': city_state_zip,
            'phone_number': phone_number,
            'dealer_code': dealer_code,
            'contact_name': contact_name,
            'outgoing_stock_number': outgoing_stock_number,
            'outgoing_year_make_model': outgoing_year_make_model,
            'outgoing_full_vin': outgoing_full_vin,
            'outgoing_sale_price': outgoing_sale_price,
            'incoming_year_make_model': incoming_year_make_model,
            'incoming_full_vin': incoming_full_vin,
            'incoming_purchase_price': incoming_purchase_price
        }

        # Create and print the PDF
        pdf_filename = "trade_document.pdf"
        create_pdf(data, pdf_filename)
        print_pdf(pdf_filename)
        st.success("Trade Submitted and Document Sent to Printer")
