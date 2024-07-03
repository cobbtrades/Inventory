import pandas as pd, streamlit as st, os, requests, base64, time, openpyxl, plotly.express as px, matplotlib.pyplot as plt, plotly.graph_objects as go
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from streamlit_extras.grid import grid

st.set_page_config(layout="wide", page_title="Nissan Inventory", page_icon="logo.png")
file_paths = ['files/Concord.xls', 'files/Winston.xls', 'files/Lake.xls', 'files/Hickory.xls']
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
    'ALTIMA': 'ALT', 'ARMADA': 'ARM', 'FRONTIER': '720', 'KICKS': 'KIX', 'LEAF ELECTRIC': 'LEF',
    'MURANO': 'MUR', 'PATHFINDER': 'PTH', 'ROGUE': 'RGE', 'SENTRA': 'SEN', 'TITAN': 'TTN',
    'VERSA': 'VSD', 'Z NISMO': 'Z', 'Z PROTO': 'Z'
}
dealer_acronyms = {
    'MODERN NISSAN OF CONCORD': 'CONCORD', 'MODERN NISSAN OF HICKORY': 'HICKORY',
    'MODERN NISSAN, LLC': 'WINSTON', 'MODERN NISSAN/LAKE NORMAN': 'LAKE'
}

@st.cache_data
def load_data(file_paths):
    expected_columns = [
        'LOC_DESC', 'DLRORD', 'MDLYR', 'MDL', 'TRM_LVL', 'DRV_TRN', 'EXT', 'INT',
        'MCODE', 'VIN', 'DEALER_NAME', 'DLR_DLV_DT', 'DLRETA', 'ORD_CUST_NAME',
        'ORD_CUST_EMAIL_ADDR', 'ORD_CUST_DATE', 'GOPTS', 'RTL_SALE_DT', 'MSRP',
    ]
    new_column_names = {
        'LOC_DESC': 'LOC', 'DLRORD': 'ORDER', 'TRM_LVL': 'TRIM', 'DRV_TRN': 'DRIVE',
        'DLRETA': 'ETA', 'ORD_CUST_NAME': 'CUST_NAME', 'ORD_CUST_EMAIL_ADDR': 'CUST_EMAIL',
        'ORD_CUST_DATE': 'ORD_DATE', 'DLR_DLV_DT': 'DLV_DATE', 'RTL_SALE_DT': 'SOLD', 'MSRP': 'MSRP'
    }
    data_frames = []
    for file in file_paths:
        if os.path.exists(file):
            dfs = pd.read_html(file)
            if dfs:
                df = dfs[0]
                df = df[[col for col in expected_columns if col in df.columns]].copy()
                df.rename(columns=new_column_names, inplace=True)
                if 'MDLYR' in df.columns:
                    df['MDLYR'] = df['MDLYR'].apply(lambda x: str(x).strip()[:-1])
                if 'MCODE' in df.columns:
                    df['MCODE'] = df['MCODE'].astype(str).str.replace(',', '')
                if 'MDL' in df.columns:
                    df['EXT'] = df['EXT'].replace(ext_mapping)
                date_columns = ['ETA', 'DLV_DATE', 'ORD_DATE', 'SOLD']
                df[date_columns] = df[date_columns].apply(lambda col: pd.to_datetime(col, errors='coerce').dt.strftime('%m-%d-%Y'))
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

data_frames = load_data(file_paths)
if data_frames:
    combined_data = pd.concat([df[0] for df in data_frames], ignore_index=True)
    combined_data.reset_index(drop=True, inplace=True)
else:
    combined_data = pd.DataFrame()
        
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

tab1, tab2, tab3, tab4, tab5 = st.tabs(["All Stores", "Current CDK", "Dealer Trade", "Incoming", "Sales"])

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

if not combined_data.empty:
    with tab1:
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            st.markdown(f"### All Stores Inventory")
        with cols[1]:
            model = st.selectbox('Model', options=['All'] + combined_data['MDL'].unique().tolist(), key='all_model')
        with cols[2]:
            trims = ['All'] if model == 'All' else ['All'] + combined_data[combined_data['MDL'] == model]['TRIM'].unique().tolist()
            trim = st.selectbox('Trim', options=trims, key='all_trim')
        with cols[3]:
            packages = ['All'] if model == 'All' else ['All'] + combined_data[combined_data['MDL'] == model]['PACKAGE'].unique().tolist()
            package = st.selectbox('Package', options=packages, key='all_package')
        with cols[4]:
            colors = ['All'] if model == 'All' else ['All'] + combined_data[combined_data['MDL'] == model]['EXT'].unique().tolist()
            color = st.selectbox('Color', options=colors, key='all_color')
        filtered_df = filter_data(combined_data, model, trim, package, color)
        st.dataframe(filtered_df, use_container_width=True, height=780, hide_index=True)
else:
    st.error("No data to display.")

with tab2:
    st.markdown("### Current CDK Inventory")
    if not current_data.empty:
        num_rows = len(current_data)
        st.markdown(f"<span style='font-size: small;'>{num_rows} vehicles</span>", unsafe_allow_html=True)
        st.dataframe(current_data, use_container_width=True, height=780, hide_index=True)
    else:
        st.error("No current inventory data to display.")

def calculate_transfer_amount(key_charge, projected_cost):
    return projected_cost - key_charge - 400

def format_currency(value):
    return "${:,.2f}".format(value)
def get_store_number(location):
    store_numbers = {
        "MODERN NISSAN OF CONCORD": "STORE #3",
        "MODERN NISSAN OF WINSTON": "STORE #2",
        "MODERN NISSAN OF LAKE NORMAN": "STORE #6",
        "MODERN NISSAN OF HICKORY": "STORE #11"
    }
    return store_numbers.get(location, "UNKNOWN STORE")

with tab3:
    st.markdown("### Dealer Trade")
    col1, col2 = st.columns(2)
    with col1:
        current_date = datetime.today()
        formatted_date = current_date.strftime("%B %d, %Y")
        st.write(f"Date: {formatted_date}")
    with col2:
        manager = st.text_input("Manager", key="manager_input_trade")
    st.markdown('<div class="small-spacing"><hr></div>', unsafe_allow_html=True)
    col3, col4, col5 = st.columns([1, 1, 2])
    with col3:
        our_trade = st.checkbox("Our Trade", key="our_trade_checkbox_trade")
        sold = st.checkbox("Sold", key="sold_checkbox_trade")
    with col4:
        their_trade = st.checkbox("Their Trade", key="their_trade_checkbox_trade")
        floorplan = st.checkbox("Floorplan", key="floorplan_checkbox_trade")
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
        from_location = st.text_input("From:", key="from_input_trade")
    with col7:
        to_location = st.selectbox("To:", 
                                   ["MODERN NISSAN OF CONCORD", 
                                    "MODERN NISSAN OF WINSTON", 
                                    "MODERN NISSAN OF LAKE NORMAN", 
                                    "MODERN NISSAN OF HICKORY"], 
                                   key="to_input_trade")
    col8, col9 = st.columns(2)
    with col8:
        stock_number = st.text_input("Stock Number", key="stock_number_input_trade")
        year_make_model = st.text_input("Year Make Model", key="year_make_model_input_trade")
        full_vin = st.text_input("Full VIN #", key="full_vin_input_trade")
    with col9:
        key_charge = st.number_input("Key Charge ($)", value=0.00, format="%.2f", key="key_charge_input_trade")
        projected_cost = st.number_input("Projected Cost ($)", value=0.00, format="%.2f", key="projected_cost_input_trade")
        transfer_amount = calculate_transfer_amount(key_charge, projected_cost)
        formatted_transfer_amount = format_currency(transfer_amount)
        st.text_input("Transfer Amount", value=formatted_transfer_amount, key="transfer_amount_input_trade", disabled=True)
        
    st.text("Non-Modern Dealership Information")
    dealership_name = st.text_input("Dealership Name", key="dealership_name_input_trade")
    address = st.text_input("Address", key="address_input_trade")
    city_state_zip = st.text_input("City, State ZIP Code", key="city_state_zip_input_trade")
    phone_number = st.text_input("Phone Number", key="phone_number_input_trade")
    dealer_code = st.text_input("Dealer Code", key="dealer_code_input_trade")
    contact_name = st.text_input("Contact Name", key="contact_name_input_trade")
    st.markdown('<div class="small-spacing"><hr></div>', unsafe_allow_html=True)
    l_col, r_col = st.columns(2)
    with l_col:
        st.text("Outgoing Unit")
        outgoing_stock_number = st.text_input("Outgoing Stock Number", key="outgoing_stock_number_input_trade")
        outgoing_year_make_model = st.text_input("Outgoing Year Make Model", key="outgoing_year_make_model_input_trade")
        outgoing_full_vin = st.text_input("Outgoing Full VIN #", key="outgoing_full_vin_input_trade")
        outgoing_sale_price = st.text_input("Outgoing Sale Price", key="outgoing_sale_price_input_trade")
        st.markdown('<div class="small-spacing"><hr></div>', unsafe_allow_html=True)
    with r_col:
        st.text("Incoming Unit")
        incoming_year_make_model = st.text_input("Incoming Year Make Model", key="incoming_year_make_model_input_trade")
        incoming_full_vin = st.text_input("Incoming Full VIN #", key="incoming_full_vin_input_trade")
        incoming_purchase_price = st.text_input("Incoming Purchase Price", key="incoming_purchase_price_input_trade")

    if st.button("Generate Trade PDF", key="generate_trade_pdf_button"):
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        offset = 20
        location = st.session_state["to_input_trade"]
        title = f"{location} {get_store_number(location)}"
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2.0, height - 52 - offset, title)
        c.setFont("Helvetica", 10)
        col1_x = 72
        col2_x = 200
        c.drawString(col1_x, height - 84 - offset, f"Date: {formatted_date}")
        c.drawString(col2_x, height - 84 - offset, f"Manager: {manager}")
        c.drawString(col1_x, height - 108 - offset, "OUR TRADE")
        c.drawString(col1_x, height - 120 - offset, f"{'         X' if our_trade else ''}")
        c.drawString(col2_x, height - 108 - offset, "THEIR TRADE")
        c.drawString(col2_x, height - 120 - offset, f"{'           X' if their_trade else ''}")
        c.drawString(col1_x, height - 144 - offset, "SOLD")
        c.drawString(col1_x, height - 156 - offset, f"{'   X' if sold else ''}")
        c.drawString(col2_x, height - 144 - offset, "FLOORPLAN")
        c.drawString(col2_x, height - 156 - offset, f"{'          X' if floorplan else ''}")
        addr_x = 320
        c.drawString(addr_x, height - 108 - offset, "PLEASE SEND MCO/CHECK TO:")
        c.drawString(addr_x, height - 120 - offset, "MODERN AUTOMOTIVE SUPPORT CENTER")
        c.drawString(addr_x, height - 132 - offset, "3901 WEST POINT BLVD.")
        c.drawString(addr_x, height - 144 - offset, "WINSTON-SALEM, NC 27103")
        c.setFillColorRGB(0.7, 0.7, 0.7)
        c.rect(70, height - 180 - offset, 475, 20, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(72, height - 175 - offset, "Intercompany DX")
        c.drawString(72, height - 200 - offset, "From:")
        c.drawString(140, height - 200 - offset, from_location)
        c.drawString(330, height - 200 - offset, "To:")
        c.drawString(380, height - 200 - offset, to_location)
        c.drawString(72, height - 220 - offset, "Stock Number:")
        c.drawString(160, height - 220 - offset, stock_number)
        c.drawString(72, height - 240 - offset, "Year/Make/Model:")
        c.drawString(160, height - 240 - offset, year_make_model)
        c.drawString(72, height - 260 - offset, "Full VIN #:")
        c.drawString(160, height - 260 - offset, full_vin)
        c.drawString(330, height - 220 - offset, "Key Charge:")
        c.drawString(420, height - 220 - offset, format_currency(key_charge))
        c.drawString(330, height - 240 - offset, "Projected Cost:")
        c.drawString(420, height - 240 - offset, format_currency(projected_cost))
        c.drawString(330, height - 260 - offset, "Transfer Amount:")
        c.drawString(420, height - 260 - offset, formatted_transfer_amount)
        c.setFillColorRGB(0.7, 0.7, 0.7)
        c.rect(70, height - 290 - offset, 475, 20, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(72, height - 285 - offset, "Non-Modern Dealership Information")
        c.drawString(72, height - 310 - offset, "Dealership Name:")
        c.drawString(190, height - 310 - offset, dealership_name)
        c.drawString(72, height - 330 - offset, "Address:")
        c.drawString(190, height - 330 - offset, address)
        c.drawString(72, height - 350 - offset, "City, State ZIP Code:")
        c.drawString(190, height - 350 - offset, city_state_zip)
        c.drawString(72, height - 370 - offset, "Phone Number:")
        c.drawString(190, height - 370 - offset, phone_number)
        c.drawString(72, height - 390 - offset, "Dealer Code:")
        c.drawString(190, height - 390 - offset, dealer_code)
        c.drawString(72, height - 410 - offset, "Contact Name:")
        c.drawString(190, height - 410 - offset, contact_name)
        c.setFillColorRGB(0.7, 0.7, 0.7)
        c.rect(70, height - 440 - offset, 475, 20, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(72, height - 435 - offset, "Outgoing Unit")
        c.drawString(72, height - 460 - offset, "Stock Number:")
        c.drawString(190, height - 460 - offset, outgoing_stock_number)
        c.drawString(72, height - 480 - offset, "Year Make Model:")
        c.drawString(190, height - 480 - offset, outgoing_year_make_model)
        c.drawString(72, height - 500 - offset, "Full VIN #:")
        c.drawString(190, height - 500 - offset, outgoing_full_vin)
        c.drawString(72, height - 520 - offset, "Sale Price:")
        c.drawString(190, height - 520 - offset, outgoing_sale_price)
        c.setFillColorRGB(0.7, 0.7, 0.7)
        c.rect(70, height - 550 - offset, 475, 20, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(72, height - 545 - offset, "Incoming Unit")
        c.drawString(72, height - 570 - offset, "Year Make Model:")
        c.drawString(190, height - 570 - offset, incoming_year_make_model)
        c.drawString(72, height - 590 - offset, "Full VIN #:")
        c.drawString(190, height - 590 - offset, incoming_full_vin)
        c.drawString(72, height - 610 - offset, "Purchase Price:")
        c.drawString(190, height - 610 - offset, incoming_purchase_price)
        c.showPage()
        c.save()
        pdf_buffer.seek(0)
        pdf_data = pdf_buffer.getvalue()
        time.sleep(0.5)
        st.download_button(label="Download Trade PDF", data=pdf_data, file_name="dealer_trade.pdf", mime="application/pdf", key="download_trade_pdf_button")

dark_mode_css = """
<style>
body {background-color: #0e1117; color: #fafafa;}
h3 {color: #fafafa;}
table {
    color: #000000;
    font-weight: bold;
    background-color: #FFFFFF;
    border: 1px solid #383e53;
    text-align: center;
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    word-wrap: break-word;
}
thead th {color: #000000; background-color: #FFFFFF; text-align: center; padding: 8px;}
tbody td {text-align: center; padding: 8px; word-wrap: break-word;}
tbody tr:nth-child(even) {background-color: #FFFFFF;}
tbody tr:nth-child(odd) {background-color: #FFFFFF;}
.dataframe-container {font-size: 12px; padding: 1px;}
.dataframe-container table {width: 100%;}
.dataframe-container th, .dataframe-container td {padding: 2px;}
.dataframe-container th {background-color: #FFFFFF;}
</style>
"""
st.markdown(dark_mode_css, unsafe_allow_html=True)

def replace_mdl_with_full_name(df, reverse_mdl_mapping):
    df['MDL'] = df['MDL'].replace(reverse_mdl_mapping)
    return df

reverse_mdl_mapping = {'ALT': 'ALTIMA', 'ARM': 'ARMADA', '720': 'FRONTIER', 'KIX': 'KICKS', 'LEF': 'LEAF',
    'MUR': 'MURANO', 'PTH': 'PATHFINDER', 'RGE': 'ROGUE', 'SEN': 'SENTRA', 'TTN': 'TITAN', 'VSD': 'VERSA',
    'ARI': 'ARIYA',  'TXD': 'TITAN XD'}

@st.cache_data
def summarize_incoming_data(df, start_date, end_date, all_models, all_dealers):
    df['ETA'] = pd.to_datetime(df['ETA'], errors='coerce')
    filtered_df = df[(df['ETA'] >= start_date) & (df['ETA'] <= end_date)]
    filtered_df['DEALER_NAME'] = filtered_df['DEALER_NAME'].replace(dealer_acronyms)
    filtered_df = replace_mdl_with_full_name(filtered_df, reverse_mdl_mapping)
    all_combinations = pd.MultiIndex.from_product([all_dealers, all_models], names=['DEALER_NAME', 'MDL'])
    summary = filtered_df.groupby(['DEALER_NAME', 'MDL']).size().reindex(all_combinations, fill_value=0).reset_index(name='Count')
    pivot_table = pd.pivot_table(summary, values='Count', index='MDL', columns='DEALER_NAME', aggfunc=sum, fill_value=0, margins=True, margins_name='Total')
    return pivot_table

def summarize_retailed_data(df, start_date, end_date, all_models, all_dealers):
    df['SOLD'] = pd.to_datetime(df['SOLD'], errors='coerce')
    df = df[df['SOLD'] >= start_date]
    filtered_df = df[(df['LOC'] == 'RETAILED')]
    filtered_df['DEALER_NAME'] = filtered_df['DEALER_NAME'].replace(dealer_acronyms)
    filtered_df = replace_mdl_with_full_name(filtered_df, reverse_mdl_mapping)
    all_combinations = pd.MultiIndex.from_product([all_dealers, all_models], names=['DEALER_NAME', 'MDL'])
    summary = filtered_df.groupby(['DEALER_NAME', 'MDL']).size().reindex(all_combinations, fill_value=0).reset_index(name='Count')
    pivot_table = pd.pivot_table(summary, values='Count', index='MDL', columns='DEALER_NAME', aggfunc=sum, fill_value=0, margins=True, margins_name='Total')
    return pivot_table

def summarize_dlv_inv_data(df, all_models, all_dealers):
    filtered_df = df[(df['LOC'] == 'DLR INV') & (df['SOLD'].isna())]
    filtered_df['DEALER_NAME'] = filtered_df['DEALER_NAME'].replace(dealer_acronyms)
    filtered_df = replace_mdl_with_full_name(filtered_df, reverse_mdl_mapping)
    all_combinations = pd.MultiIndex.from_product([all_dealers, all_models], names=['DEALER_NAME', 'MDL'])
    summary = filtered_df.groupby(['DEALER_NAME', 'MDL']).size().reindex(all_combinations, fill_value=0).reset_index(name='Count')
    pivot_table = pd.pivot_table(summary, values='Count', index='MDL', columns='DEALER_NAME', aggfunc=sum, fill_value=0, margins=True, margins_name='Total')
    return pivot_table

def summarize_dlv_date_data(df, start_date, end_date, all_models, all_dealers):
    df['DLV_DATE'] = pd.to_datetime(df['DLV_DATE'], errors='coerce')
    filtered_df = df[(df['DLV_DATE'] >= start_date) & (df['DLV_DATE'] <= end_date)]
    filtered_df['DEALER_NAME'] = filtered_df['DEALER_NAME'].replace(dealer_acronyms)
    filtered_df = replace_mdl_with_full_name(filtered_df, reverse_mdl_mapping)
    all_combinations = pd.MultiIndex.from_product([all_dealers, all_models], names=['DEALER_NAME', 'MDL'])
    summary = filtered_df.groupby(['DEALER_NAME', 'MDL']).size().reindex(all_combinations, fill_value=0).reset_index(name='Count')
    pivot_table = pd.pivot_table(summary, values='Count', index='MDL', columns='DEALER_NAME', aggfunc=sum, fill_value=0, margins=True, margins_name='Total')
    return pivot_table

def dataframe_to_html(df):
    html = df.to_html(classes='dataframe-container', border=0, index_names=False)
    return html

with tab4:
    container = st.container()
    if not combined_data.empty:
        today = datetime.today()
        start_of_month = today.replace(day=1)
        next_month_start = start_of_month.replace(month=start_of_month.month + 1).replace(day=1)
        following_month_start = start_of_month.replace(month=start_of_month.month + 2).replace(day=1)
        start_for_calc = start_of_month.replace(month=start_of_month.month + 3).replace(day=1)
        end_of_month = next_month_start - timedelta(days=1)
        next_month_end = following_month_start - timedelta(days=1)
        following_month_end = start_for_calc - timedelta(days=1)
        all_models = combined_data['MDL'].replace(reverse_mdl_mapping).unique()
        all_dealers = combined_data['DEALER_NAME'].replace(dealer_acronyms).unique()
        with container:
            blank_col1, col1, col2, col3, blank_col2 = st.columns([0.1, 1, 1, 1, 0.1])
            with col1:
                st.markdown(f"<h5 style='text-align: center;'>Incoming for {start_of_month.strftime('%B')}</h5>", unsafe_allow_html=True)
                current_month_summary = summarize_incoming_data(combined_data, start_of_month, end_of_month, all_models, all_dealers)
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html(current_month_summary)}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<h5 style='text-align: center;'>RETAILED</h5>", unsafe_allow_html=True)
                retailed_summary = summarize_retailed_data(combined_data, start_of_month, end_of_month, all_models, all_dealers)
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html(retailed_summary)}</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"<h5 style='text-align: center;'>Incoming for {next_month_start.strftime('%B')}</h5>", unsafe_allow_html=True)
                next_month_summary = summarize_incoming_data(combined_data, next_month_start, next_month_end, all_models, all_dealers)
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html(next_month_summary)}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<h5 style='text-align: center;'>Current NNA Inventory(DLR INV)</h5>", unsafe_allow_html=True)
                dlv_inv_summary = summarize_dlv_inv_data(combined_data, all_models, all_dealers)
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html(dlv_inv_summary)}</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"<h5 style='text-align: center;'>Incoming for {following_month_start.strftime('%B')}</h5>", unsafe_allow_html=True)
                following_month_summary = summarize_incoming_data(combined_data, following_month_start, following_month_end, all_models, all_dealers)
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html(following_month_summary)}</div>", unsafe_allow_html=True)
                
                current_month_dlv_summary = summarize_dlv_date_data(combined_data, start_of_month, end_of_month, all_models, all_dealers)
                balance_to_arrive = current_month_summary.subtract(current_month_dlv_summary, fill_value=0)
                st.markdown(f"<h5 style='text-align: center;'>Balance to Arrive for {start_of_month.strftime('%B')}</h5>", unsafe_allow_html=True)
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html(balance_to_arrive)}</div>", unsafe_allow_html=True)
    else:
        st.error("No data to display.")

def plot_metric(dataframes, metric, title, ylabel):
    fig = go.Figure()
    
    bar_width = 0.2
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Custom color palette for better contrast

    for i, (name, df) in enumerate(dataframes.items()):
        fig.add_trace(go.Bar(
            x=df['Model'],
            y=df[metric],
            name=name,
            marker_color=colors[i]
        ))

    fig.update_layout(
        title=title,
        xaxis_title='Model',
        yaxis_title=ylabel,
        barmode='group',
        bargap=0.2,
        bargroupgap=0.1,
        plot_bgcolor='#ffffff',
        paper_bgcolor='#0e1117',
        font=dict(color='#d0d0d0')
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    def process_excel(file):
        df = pd.read_html(file)[0].iloc[:, :9]
        df.columns = df.iloc[1]
        df = df.drop([0, 1])
        df.columns = ['Model', 'Sold Roll 90', 'Sold-MTD', 'Dlr Invoice', 'Dlr Inventory', 'Days Supply',
                      'Wholesale to Retail Dealer(avg days)', 'Wholesale to Retail District(avg days)', 'Wholesale to Retail Region(avg days)']
        df['Model'] = df['Model'].astype(str)
        numeric_columns = ['Sold Roll 90', 'Sold-MTD', 'Dlr Invoice', 'Dlr Inventory', 'Days Supply',
                           'Wholesale to Retail Dealer(avg days)', 'Wholesale to Retail District(avg days)', 'Wholesale to Retail Region(avg days)']
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
        df = df.dropna(subset=['Model'])
        return df
    
    cn_df = process_excel('files/Concord90.xls')
    hk_df = process_excel('files/Hickory90.xls')
    ln_df = process_excel('files/Lake90.xls')
    ws_df = process_excel('files/Winston90.xls')

    dataframes = {
        'Concord': cn_df,
        'Hickory': hk_df,
        'Lake': ln_df,
        'Winston': ws_df
    }
    
    bl1, col1, col2, bl2 = st.columns([0.1, 1, 1, 0.1])
    with col1:
        plot_metric(dataframes, 'Sold Roll 90', 'Sales Trends Over the Last 90 Days', 'Sold Roll 90')
        plot_metric(dataframes, 'Sold-MTD', 'Month-to-Date Sales Performance', 'Sold-MTD')
    
    with col2:
        plot_metric(dataframes, 'Days Supply', 'Inventory Levels (Days Supply)', 'Days Supply')
        plot_metric(dataframes, 'Dlr Inventory', 'Dealer Inventory Comparison', 'Dlr Inventory')
