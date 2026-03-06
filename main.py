import pandas as pd, streamlit as st, os, time, plotly.graph_objects as go, plotly.express as px, warnings, numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import shutil
from pathlib import Path
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

st.set_page_config(layout="wide", page_title="Nissan Inventory", page_icon="logo.png", initial_sidebar_state="collapsed")

# Ensure files directory exists
files_dir = Path("files")
files_dir.mkdir(exist_ok=True)

# File upload and management functions
def save_uploaded_files(uploaded_files):
    """Save uploaded files to the appropriate directory and clear cache."""
    if uploaded_files:
        saved_files = []
        for uploaded_file in uploaded_files:
            # Save InventoryUpdate.xlsx to root, others to files directory
            if uploaded_file.name == "InventoryUpdate.xlsx":
                file_path = Path(uploaded_file.name)
            else:
                file_path = files_dir / uploaded_file.name
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            saved_files.append(uploaded_file.name)
        # Clear all caches to reload data
        st.cache_data.clear()
        return saved_files
    return []

def get_file_paths():
    """Get file paths, checking if files exist."""
    file_paths = ['files/Concord.xls', 'files/Winston.xls', 'files/Lake.xls', 'files/Hickory.xls']
    return [fp for fp in file_paths if os.path.exists(fp)]

file_paths = get_file_paths()
store_files = {
    "Concord": "files/Concord90.xls",
    "Hickory": "files/Hickory90.xls",
    "Lake Norman": "files/Lake90.xls",
    "Winston-Salem": "files/Winston90.xls",
}
ext_mapping = {
    'A20': 'RED ALERT', 'B51': 'ELECTRIC BLUE', 'BW5': 'HERMOSA BLUE', 'CAS': 'MOCHA ALMOND',
    'CBF': 'CANYON BRONZE', 'XLC': 'GUN/RED', 'XLE': 'YELLOW/BLACK', 'XLD': 'ICE/BLACK',
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
    'NCA': 'BURGUNDY', 'QBE': 'EVEREST WHITE', 'KBZ': 'ATLANTIC GRAY', 'XKY': 'ATLANTIC/BLACK',
    'XKJ': 'EVEREST/BLACK', 'RCF': 'BLUESTONE PEARL', 'XHQ': 'DEEP OCEAN/BLACK', 'XJR': 'SEIRAN BLUE/BLACK',
    'XHN': 'BLU/GRAY', 'XHN': 'BLUE/GRAY', 'ECG': 'ORANGE', 'ECD': 'ORANGE', 'DAR': 'ALPINE',
    'XKN': 'AURORA/BLACK', 'FAN': 'AURORA', 'KCF': 'CHAMPAGNE', 'XLW': 'ALPINE/BLACK',
    'XBF': 'SILVER/BLACK', 'YCU': 'RED/BLACK',
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

dlr_acronyms = {
    'Concord': 'CONCORD', 'Hickory': 'HICKORY', 'Lake Norman': 'LAKE',
    'Winston-Salem': 'WINSTON'
}

excluded_dealers = ["NISSAN OF BOONE", "EAST CHARLOTTE NISSAN"]

def clean_dataframe_types(df):
    """Ensure all dataframe columns have consistent, Arrow-compatible types."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':
            # Convert all object columns to string, handling NaN values
            df[col] = df[col].astype(str).replace('nan', '').replace('None', '')
        elif pd.api.types.is_numeric_dtype(df[col]):
            # Ensure numeric columns are properly typed
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

@st.cache_data
def load_data(file_paths):
    expected_columns = [
        'LOC_DESC', 'DLRORD', 'MDLYR', 'MDL', 'TRM_LVL', 'DRV_TRN', 'EXT', 'INT',
        'MCODE', 'VIN', 'DEALER_NAME', 'DLR_DLV_DT', 'DLRETA', 'ORD_CUST_NAME',
        'ORD_CUST_EMAIL_ADDR', 'ORD_CUST_DATE', 'GOPTS', 'RTL_SALE_DT'
    ]
    new_column_names = {
        'LOC_DESC': 'LOC', 'DLRORD': 'ORDER', 'TRM_LVL': 'TRIM', 'DRV_TRN': 'DRIVE',
        'DLRETA': 'ETA', 'ORD_CUST_NAME': 'CUST_NAME', 'ORD_CUST_EMAIL_ADDR': 'CUST_EMAIL',
        'ORD_CUST_DATE': 'ORD_DATE', 'DLR_DLV_DT': 'DLV_DATE', 'RTL_SALE_DT': 'SOLD'
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
                df['Premium'] = df['GOPTS'].apply(lambda x: 'PRM' if pd.notna(x) and isinstance(x, str) and any(sub in x for sub in ['PRM', 'PR1', 'PR2', 'PR3']) else '')
                df['Technology'] = df['GOPTS'].apply(lambda x: 'TECH' if pd.notna(x) and isinstance(x, str) and any(sub in x for sub in ['TEC', 'TE1', 'TE2', 'TE3']) else '')
                df['Convenience'] = df['GOPTS'].apply(lambda x: 'CONV' if pd.notna(x) and isinstance(x, str) and any(sub in x for sub in ['CN1', 'CN2', 'CN3', 'CN4', 'CN5']) else '')
                df['PACKAGE'] = df[['Premium', 'Technology', 'Convenience']].apply(lambda x: ' '.join(filter(None, x)), axis=1)
                df.drop(columns=['Premium', 'Technology', 'Convenience', 'GOPTS'], inplace=True)
                cols = df.columns.tolist()
                drive_index = cols.index('DRIVE')
                cols.insert(drive_index + 1, cols.pop(cols.index('PACKAGE')))
                df = df[cols]
                df.sort_values(by='MDL', inplace=True)
                df.reset_index(drop=True, inplace=True)
                # Clean dataframe types to ensure Arrow compatibility
                df = clean_dataframe_types(df)
                data_frames.append((df, file))
        else:
            st.error(f"File {file} not found in the repository.")
    return data_frames

def add_unit_key(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    vin = df['VIN'].astype(str).str.strip()
    order = df['ORDER'].astype(str).str.strip()
    df['UNIT_KEY'] = np.where(vin != '', vin, order)
    return df

# Load data with error handling
try:
    data_frames = load_data(file_paths)
    if data_frames:
        frames = []
        for df, _ in data_frames:
            tmp = add_unit_key(df)
            tmp['ETA_DT'] = pd.to_datetime(tmp['ETA'], errors='coerce')
            tmp.sort_values(['DEALER_NAME', 'UNIT_KEY', 'ETA_DT'], inplace=True, na_position='last')
            tmp = tmp.drop_duplicates(subset=['DEALER_NAME', 'UNIT_KEY'], keep='last')
            frames.append(tmp.drop(columns=['ETA_DT']))
        combined_data = pd.concat(frames, ignore_index=True)
        combined_data.reset_index(drop=True, inplace=True)
        # Clean types after concatenation to ensure Arrow compatibility
        combined_data = clean_dataframe_types(combined_data)
    else:
        combined_data = pd.DataFrame()
except Exception as e:
    st.warning(f"⚠️ Error loading data: {str(e)}. Please check your uploaded files.")
    combined_data = pd.DataFrame()
        
@st.cache_data
def load_current_data(file_path):
    if os.path.exists(file_path):
        df = pd.read_excel(file_path, header=4, usecols='B:O')
        del df['Deal \nNo.']
        del df['Make']
        df.columns = [
            'STOCK', 'YEAR', 'MDL', 'MCODE', 'COLOR', 'LOT', 'COMPANY',
            'AGE', 'STATUS', 'VIN', 'BALANCE', 'CUSTOM'
        ]
        df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce').fillna(0).astype(int)
        df['BALANCE'] = pd.to_numeric(df['BALANCE'], errors='coerce').fillna(0.0)
        df['COLOR'] = df['COLOR'].apply(
            lambda x: ext_mapping.get(str(x)[:3], x) if isinstance(x, str) else x
        )
        df['MCODE'] = df['MCODE'].astype(str).str.replace(',', '', regex=False)
        df['MDL']   = df['MDL'].replace(mdl_mapping)
        df.sort_values(by='COMPANY', inplace=True)
        df.reset_index(drop=True, inplace=True)
        # Clean types to ensure Arrow compatibility
        df = clean_dataframe_types(df)
        return df
    else:
        st.error(f"File {file_path} not found.")
        return pd.DataFrame()

# Load current data with error handling
try:
    if os.path.exists('InventoryUpdate.xlsx'):
        current_data = load_current_data('InventoryUpdate.xlsx')
    else:
        current_data = pd.DataFrame()
except Exception as e:
    st.warning(f"⚠️ Error loading current inventory data: {str(e)}")
    current_data = pd.DataFrame()

@st.cache_data
def process_90_day_sales(file_path):
    """Process the 90-day sales data for a given file."""
    try:
        data = pd.read_html(file_path)[0]
        cleaned_data = data.iloc[2:, :9]  # Ignore headers and excess columns
        cleaned_data.columns = [
            "Model",
            "Units Sold Rolling Days 90",
            "Units Sold-MTD",
            "Dlr Invoice",
            "Dlr Inventory",  # Current Inventory
            "Dlr Days Supply",
            "Wholesale to Retail Dealer (avg days)",
            "Wholesale to Retail District (avg days)",
            "Wholesale to Retail Region (avg days)",
        ]
        numeric_columns = [
            "Units Sold Rolling Days 90",
            "Units Sold-MTD",
            "Dlr Invoice",
            "Dlr Inventory",
            "Dlr Days Supply",
            "Wholesale to Retail Dealer (avg days)",
            "Wholesale to Retail District (avg days)",
            "Wholesale to Retail Region (avg days)",
        ]
        cleaned_data[numeric_columns] = cleaned_data[numeric_columns].apply(pd.to_numeric, errors="coerce")
        cleaned_data = cleaned_data.dropna(subset=["Model"])
        return cleaned_data
    except Exception as e:
        st.error(f"Error processing file {file_path}: {e}")
        return pd.DataFrame()

# Load data for all stores with error handling
store_summaries = {}
for store, file_path in store_files.items():
    try:
        if os.path.exists(file_path):
            store_summaries[store] = process_90_day_sales(file_path)
        else:
            store_summaries[store] = pd.DataFrame(columns=["Model", "Units Sold Rolling Days 90"])
    except Exception as e:
        store_summaries[store] = pd.DataFrame(columns=["Model", "Units Sold Rolling Days 90"])

@st.cache_data
def summarize_90_day_sales_by_store():
    try:
        filtered_summaries = {
            store: df for store, df in store_summaries.items()
            if store.upper() != "NISSAN OF BOONE" and store.upper() != "EAST CHARLTOTE NISSAN" and not df.empty
        }
        all_stores_summary = pd.concat(
            {store: df.set_index("Model")[["Units Sold Rolling Days 90"]] for store, df in filtered_summaries.items()},
            axis=1
        ).fillna(0)
        all_stores_summary.columns = all_stores_summary.columns.get_level_values(0)
        all_stores_summary.reset_index(inplace=True)
        summary_long = all_stores_summary.melt(
            id_vars=["Model"], 
            var_name="Dealer", 
            value_name="Units Sold Rolling Days 90"
        )
        return summary_long
    except Exception as e:
        st.error(f"Error summarizing 90-day sales: {e}")
        return pd.DataFrame(columns=["Model", "Dealer", "Units Sold Rolling Days 90"])
        
@st.cache_data
def format_90_day_sales(summary_90_day_sales):
    formatted_summary = summary_90_day_sales.pivot_table(
        values="Units Sold Rolling Days 90",
        index="Model",
        columns="Dealer",
        aggfunc="sum",
        fill_value=0
    )
    formatted_summary["Total"] = formatted_summary.sum(axis=1)
    formatted_summary = formatted_summary.reset_index()
    formatted_summary = formatted_summary[~formatted_summary["Model"].isin(["GT-R", "TITAN XD", "TOTAL"])]
    formatted_summary.columns = [
        dlr_acronyms.get(col, col) if col != "Model" else col
        for col in formatted_summary.columns
    ]
    total_row = formatted_summary.drop(columns=["Model"]).sum(numeric_only=True)
    total_row["Model"] = "Total"
    formatted_summary = formatted_summary.sort_values(
        by="Model",
        key=lambda x: x.str.lower() if x.name == "Model" else x,
        ignore_index=True
    )
    formatted_summary = pd.concat(
        [formatted_summary, pd.DataFrame([total_row])],
        ignore_index=True
    )
    return formatted_summary

summary_90_day_sales = summarize_90_day_sales_by_store()
formatted_90_day_sales = format_90_day_sales(summary_90_day_sales)

# Modern UI Styling
modern_css = """
<style>
    /* Main container styling - ZERO top padding */
    .main .block-container {
        padding-top: 0rem !important;
        padding-left: 3rem;
        padding-right: 3rem;
        padding-bottom: 3rem;
        margin-top: 0 !important;
    }
    
    /* Remove ALL top spacing from Streamlit - comprehensive targeting */
    .main .block-container > *:first-child,
    .main .block-container > div:first-child,
    .main .block-container > section:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove Streamlit default spacing on all first elements */
    .element-container:first-child,
    div[data-testid="stVerticalBlock"]:first-child,
    section[data-testid="stVerticalBlock"]:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove spacing from expander when it's first - more aggressive */
    .streamlit-expander:first-child,
    div[data-testid="stExpander"]:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Override Streamlit's default top padding on all containers */
    section[data-testid="stAppViewContainer"] > div:first-child,
    section[data-testid="stAppViewContainer"] > div > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Target the specific div that wraps everything */
    div[data-testid="stAppViewContainer"] > div > div > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #c3002f 0%, #7a001d 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* File upload area styling */
    .upload-section {
        background: #1a1a1a;
        padding: 1.5rem;
        border-radius: 15px;
        border: 2px dashed #c3002f;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    /* Reduce expander spacing - completely remove top spacing */
    .streamlit-expanderHeader,
    div[data-testid="stExpander"] > div:first-child {
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        padding-top: 0.25rem !important;
    }
    
    /* Remove top margin from expander content */
    .streamlit-expanderContent {
        margin-top: 0 !important;
    }
    
    /* Target the expander wrapper directly */
    div[data-testid="stExpander"] {
        margin-top: 0 !important;
    }
    
    .upload-section:hover {
        border-color: #ff1744;
        background: #202020;
    }
    
    /* Tabs container */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: #151515;
        padding: 10px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    
    /* Individual tabs */
    .stTabs [data-baseweb="tab"] {
        background: #202020;
        color: #dcdcdc;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
        border: 1px solid rgba(255,255,255,0.06);
        transition: all 0.25s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #2a2a2a;
        color: white;
    }
    
    /* Active tab */
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #c3002f 0%, #7a001d 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(195, 0, 47, 0.35);
    }
    
    /* Success message styling */
    .success-box {
        background: linear-gradient(135deg, #0f9d58 0%, #34a853 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: 600;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Metric cards */
    .metric-card {
        background: #1a1a1a;
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        border-left: 4px solid #c3002f;
    }
    
    /* Dataframe styling */
    table {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
    }
    
    thead th {
        background: linear-gradient(135deg, #c3002f 0%, #7a001d 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 12px !important;
    }
    
    tbody tr {
        transition: background-color 0.2s ease;
    }
    
    tbody tr:hover {
        background-color: #2a2a2a !important;
    }
    
    tbody tr:nth-child(even) {
        background-color: #1b1b1b;
        color: #e5e5e5;
    }
    
    tbody tr:nth-child(odd) {
        background-color: #141414;
        color: #e5e5e5;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #c3002f 0%, #7a001d 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(195, 0, 47, 0.35);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(195, 0, 47, 0.5);
    }
    
    /* Selectbox / dropdown field */
    .stSelectbox > div > div,
    div[data-baseweb="select"] > div {
        background-color: #1a1a1a !important;
        color: white !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }
    
    /* Selected value text */
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
        color: white !important;
    }
    
    /* Dropdown menu */
    div[role="listbox"] {
        background-color: #1a1a1a !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: white !important;
    }
    
    /* Dropdown options */
    div[role="option"] {
        background-color: #1a1a1a !important;
        color: white !important;
    }
    
    div[role="option"]:hover {
        background-color: #2a2a2a !important;
        color: white !important;
    }
    
    /* Inputs */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 8px !important;
    }
    
    /* Labels */
    label, .stMarkdown, p, h1, h2, h3, h4, h5, h6 {
        color: #e5e5e5;
    }
    
    /* App background */
    .stApp {
        background-color: #0e1117;
        color: #e5e5e5;
    }
    
    /* Hide Streamlit branding and header completely */
    #MainMenu {visibility: hidden; height: 0 !important;}
    footer {visibility: hidden; height: 0 !important;}
    header {visibility: hidden; height: 0 !important;}
    
    /* Remove header spacing completely */
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Remove any top spacing from the app view - multiple selectors */
    section[data-testid="stAppViewContainer"],
    div[data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Ensure main content starts at the very top */
    .main,
    div[class*="main"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Target the root app div */
    #root > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove any spacing from body/html */
    body {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Force remove top spacing with negative margin as last resort */
    .main .block-container:first-child {
        margin-top: -2rem !important;
    }
    
    /* Target the very first element */
    .main > div:first-child > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #161616;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #c3002f 0%, #7a001d 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #c3002f;
    }
</style>
"""
st.markdown(modern_css, unsafe_allow_html=True)

# JavaScript to force remove top spacing (runs after page load)
st.markdown("""
<script>
    // Remove top spacing immediately and on load
    function removeTopSpacing() {
        // Target all possible containers
        const containers = [
            '.main .block-container',
            'section[data-testid="stAppViewContainer"]',
            '.main',
            'div[data-testid="stVerticalBlock"]:first-child',
            '.streamlit-expander:first-child'
        ];
        
        containers.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el) {
                    el.style.marginTop = '0px';
                    el.style.paddingTop = '0px';
                }
            });
        });
        
        // Specifically target first expander
        const firstExpander = document.querySelector('.streamlit-expander:first-child');
        if (firstExpander) {
            firstExpander.style.marginTop = '0px';
            firstExpander.style.paddingTop = '0px';
        }
    }
    
    // Run immediately
    removeTopSpacing();
    
    // Run on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', removeTopSpacing);
    } else {
        removeTopSpacing();
    }
    
    // Run after a short delay to catch dynamically loaded content
    setTimeout(removeTopSpacing, 100);
    setTimeout(removeTopSpacing, 500);
</script>
""", unsafe_allow_html=True)

# File Upload Section
with st.expander("📁 Upload Files - Drag & Drop Your Files Folder Here", expanded=False):
    
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=['xls', 'xlsx'],
        accept_multiple_files=True,
        help="Select one or more Excel files to upload. Files will be saved to the files folder and the app will refresh automatically."
    )
    
    if uploaded_files:
        if st.button("💾 Save Files & Refresh Data", type="primary", width='stretch'):
            saved = save_uploaded_files(uploaded_files)
            if saved:
                st.markdown(f"""
                <div class="success-box">
                    ✅ Successfully uploaded {len(saved)} file(s): {', '.join(saved)}
                    <br>🔄 Refreshing data...
                </div>
                """, unsafe_allow_html=True)
                st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏪 All Stores", "💼 Current CDK", "🔄 Dealer Trade", "📥 Incoming", "📊 Sales"])

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
            total_vehicles = len(combined_data)
            st.metric("Total Vehicles", f"{total_vehicles:,}")
        with cols[1]:
            model = st.selectbox('🚗 Model', options=['All'] + sorted(combined_data['MDL'].unique().tolist()), key='all_model')
        with cols[2]:
            trims = ['All'] if model == 'All' else ['All'] + sorted(combined_data[combined_data['MDL'] == model]['TRIM'].unique().tolist())
            trim = st.selectbox('✨ Trim', options=trims, key='all_trim')
        with cols[3]:
            packages = ['All'] if model == 'All' else ['All'] + sorted([p for p in combined_data[combined_data['MDL'] == model]['PACKAGE'].unique().tolist() if p and str(p) != 'nan'])
            package = st.selectbox('📦 Package', options=packages, key='all_package')
        with cols[4]:
            colors = ['All'] if model == 'All' else ['All'] + sorted(combined_data[combined_data['MDL'] == model]['EXT'].unique().tolist())
            color = st.selectbox('🎨 Color', options=colors, key='all_color')
        filtered_df = filter_data(combined_data, model, trim, package, color)
        st.markdown(f"**Showing {len(filtered_df)} vehicle(s)**")
        st.dataframe(filtered_df, height=780, hide_index=True, width='stretch')
else:
    st.error("❌ No data to display. Please upload files using the file upload section above.")

with tab2:
    if not current_data.empty:
        num_rows = len(current_data)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Vehicles", f"{num_rows:,}")
        with col2:
            avg_age = current_data['AGE'].mean() if 'AGE' in current_data.columns else 0
            st.metric("Avg Age (Days)", f"{avg_age:.1f}")
        st.dataframe(current_data, height=780, hide_index=True, width='stretch')
    else:
        st.error("❌ No current inventory data to display. Please upload InventoryUpdate.xlsx file.")

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
        sold     = st.checkbox("Sold",     key="sold_checkbox_trade")
    with col4:
        their_trade = st.checkbox("Their Trade", key="their_trade_checkbox_trade")
        floorplan   = st.checkbox("Floorplan",   key="floorplan_checkbox_trade")
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
        to_location = st.selectbox(
            "To:", 
            [
                "MODERN NISSAN OF CONCORD", 
                "MODERN NISSAN OF WINSTON", 
                "MODERN NISSAN OF LAKE NORMAN", 
                "MODERN NISSAN OF HICKORY"
            ], 
            key="to_input_trade"
        )

    col8, col9 = st.columns(2)
    with col8:
        stock_number      = st.text_input("Stock Number", key="stock_number_input_trade")
        year_make_model   = st.text_input("Year Make Model", key="year_make_model_input_trade")
        full_vin          = st.text_input("Full VIN #", key="full_vin_input_trade")
    with col9:
        projected_cost    = st.number_input(
                                "Projected Cost ($)", 
                                value=0.00, 
                                format="%.2f", 
                                key="projected_cost_input_trade"
                            )
        formatted_projected_cost = format_currency(projected_cost)

    st.text("Non-Modern Dealership Information")
    dealership_name = st.text_input("Dealership Name", key="dealership_name_input_trade")
    address         = st.text_input("Address", key="address_input_trade")
    city_state_zip  = st.text_input("City, State ZIP Code", key="city_state_zip_input_trade")
    phone_number    = st.text_input("Phone Number", key="phone_number_input_trade")
    dealer_code     = st.text_input("Dealer Code", key="dealer_code_input_trade")
    contact_name    = st.text_input("Contact Name", key="contact_name_input_trade")

    st.markdown('<div class="small-spacing"><hr></div>', unsafe_allow_html=True)
    l_col, r_col = st.columns(2)
    with l_col:
        st.text("Outgoing Unit")
        outgoing_stock_number        = st.text_input("Outgoing Stock Number",       key="outgoing_stock_number_input_trade")
        outgoing_year_make_model     = st.text_input("Outgoing Year Make Model",    key="outgoing_year_make_model_input_trade")
        outgoing_full_vin            = st.text_input("Outgoing Full VIN #",         key="outgoing_full_vin_input_trade")
        outgoing_sale_price          = st.text_input("Outgoing Sale Price",         key="outgoing_sale_price_input_trade")
        outgoing_projected_cost      = st.number_input(
                                           "Outgoing Projected Cost ($)",
                                           value=0.00,
                                           format="%.2f",
                                           key="outgoing_projected_cost_input_trade"
                                       )
        formatted_outgoing_proj_cost = format_currency(outgoing_projected_cost)
    with r_col:
        st.text("Incoming Unit")
        incoming_year_make_model     = st.text_input("Incoming Year Make Model", key="incoming_year_make_model_input_trade")
        incoming_full_vin            = st.text_input("Incoming Full VIN #",       key="incoming_full_vin_input_trade")
        incoming_purchase_price      = st.text_input("Incoming Purchase Price",   key="incoming_purchase_price_input_trade")

    if st.button("Generate Trade PDF", key="generate_trade_pdf_button"):
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        offset = 20

        # Header
        location = st.session_state["to_input_trade"]
        title = f"{location} {get_store_number(location)}"
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2.0, height - 52 - offset, title)
        c.setFont("Helvetica", 10)
        col1_x = 72
        col2_x = 200

        # Date & Manager
        c.drawString(col1_x, height - 84 - offset, f"Date: {formatted_date}")
        c.drawString(col2_x, height - 84 - offset, f"Manager: {manager}")

        # Trade Checkboxes
        c.drawString(col1_x, height - 108 - offset, "OUR TRADE")
        c.drawString(col1_x, height - 120 - offset, f"{'         X' if our_trade else ''}")
        c.drawString(col2_x, height - 108 - offset, "THEIR TRADE")
        c.drawString(col2_x, height - 120 - offset, f"{'           X' if their_trade else ''}")
        c.drawString(col1_x, height - 144 - offset, "SOLD")
        c.drawString(col1_x, height - 156 - offset, f"{'   X' if sold else ''}")
        c.drawString(col2_x, height - 144 - offset, "FLOORPLAN")
        c.drawString(col2_x, height - 156 - offset, f"{'          X' if floorplan else ''}")

        # Address block
        addr_x = 320
        c.drawString(addr_x, height - 108 - offset, "PLEASE SEND MCO/CHECK TO:")
        c.drawString(addr_x, height - 120 - offset, "MODERN AUTOMOTIVE SUPPORT CENTER")
        c.drawString(addr_x, height - 132 - offset, "3901 WEST POINT BLVD.")
        c.drawString(addr_x, height - 144 - offset, "WINSTON-SALEM, NC 27103")

        # Intercompany DX bar
        c.setFillColorRGB(0.7, 0.7, 0.7)
        c.rect(70, height - 180 - offset, 475, 20, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(72, height - 175 - offset, "Intercompany DX")

        # From / To
        c.drawString(72, height - 200 - offset, "From:")
        c.drawString(140, height - 200 - offset, from_location)
        c.drawString(330, height - 200 - offset, "To:")
        c.drawString(380, height - 200 - offset, to_location)

        # Vehicle Info
        c.drawString(72, height - 220 - offset, "Stock Number:")
        c.drawString(160, height - 220 - offset, stock_number)
        c.drawString(72, height - 240 - offset, "Year/Make/Model:")
        c.drawString(160, height - 240 - offset, year_make_model)
        c.drawString(72, height - 260 - offset, "Full VIN #:")
        c.drawString(160, height - 260 - offset, full_vin)

        # Projected Cost (header)
        c.drawString(330, height - 220 - offset, "Projected Cost:")
        c.drawString(420, height - 220 - offset, formatted_projected_cost)

        # Non-Modern Dealership header
        c.setFillColorRGB(0.7, 0.7, 0.7)
        c.rect(70, height - 290 - offset, 475, 20, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(72, height - 285 - offset, "Non-Modern Dealership Information")

        # Non-Modern fields
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

        # Outgoing Unit header
        c.setFillColorRGB(0.7, 0.7, 0.7)
        c.rect(70, height - 440 - offset, 475, 20, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(72, height - 435 - offset, "Outgoing Unit")

        # Outgoing fields
        c.drawString(72, height - 460 - offset, "Stock Number:")
        c.drawString(190, height - 460 - offset, outgoing_stock_number)
        c.drawString(72, height - 480 - offset, "Year Make Model:")
        c.drawString(190, height - 480 - offset, outgoing_year_make_model)
        c.drawString(72, height - 500 - offset, "Full VIN #:")
        c.drawString(190, height - 500 - offset, outgoing_full_vin)
        c.drawString(72, height - 520 - offset, "Sale Price:")
        c.drawString(190, height - 520 - offset, outgoing_sale_price)
        c.drawString(72, height - 540 - offset, "Projected Cost:")
        c.drawString(190, height - 540 - offset, formatted_outgoing_proj_cost)

        # Incoming Unit header
        c.setFillColorRGB(0.7, 0.7, 0.7)
        c.rect(70, height - 570 - offset, 475, 20, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(72, height - 565 - offset, "Incoming Unit")

        # Incoming fields
        c.drawString(72, height - 590 - offset, "Year Make Model:")
        c.drawString(190, height - 590 - offset, incoming_year_make_model)
        c.drawString(72, height - 610 - offset, "Full VIN #:")
        c.drawString(190, height - 610 - offset, incoming_full_vin)
        c.drawString(72, height - 630 - offset, "Purchase Price:")
        c.drawString(190, height - 630 - offset, incoming_purchase_price)

        c.showPage()
        c.save()
        pdf_buffer.seek(0)

        pdf_data = pdf_buffer.getvalue()
        time.sleep(0.5)
        st.download_button(
            label="Download Trade PDF",
            data=pdf_data,
            file_name="dealer_trade.pdf",
            mime="application/pdf",
            key="download_trade_pdf_button"
        )

# Additional styling for dataframes in tabs
dataframe_css = """
<style>
.dataframe-container {
    font-size: 12px;
    padding: 1px;
    border-radius: 10px;
    overflow: hidden;
}
.dataframe-container table {
    width: 100%;
    border-radius: 10px;
}
.dataframe-container th, .dataframe-container td {
    padding: 8px;
}
.dataframe-container th {
    background: linear-gradient(135deg, #c3002f 0%, #7a001d 100%);
    color: white;
    font-weight: 700;
    text-align: center !important;
}
/* Center all cells except the first column (Model column) */
.dataframe-container td {
    text-align: center !important;
    background-color: #ffffff !important;
    color: #000000 !important;
}
.dataframe-container td:first-child,
.dataframe-container th:first-child {
    text-align: left !important;
}
/* Ensure all table cells have white background and black text */
.dataframe-container tbody tr {
    background-color: #ffffff !important;
}
.dataframe-container tbody tr:nth-child(even) {
    background-color: #ffffff !important;
    color: #000000 !important;
}
.dataframe-container tbody tr:nth-child(odd) {
    background-color: #ffffff !important;
    color: #000000 !important;
}
.dataframe-container tbody tr:hover {
    background-color: #f5f5f5 !important;
}
.dataframe-container tbody td {
    background-color: #ffffff !important;
    color: #000000 !important;
}
</style>
"""
st.markdown(dataframe_css, unsafe_allow_html=True)

def replace_mdl_with_full_name(df, reverse_mdl_mapping):
    df['MDL'] = df['MDL'].replace(reverse_mdl_mapping)
    return df

reverse_mdl_mapping = {'ALT': 'ALTIMA', 'ARM': 'ARMADA', '720': 'FRONTIER', 'KIX': 'KICKS', 'LEF': 'LEAF',
    'MUR': 'MURANO', 'PTH': 'PATHFINDER', 'RGE': 'ROGUE', 'SEN': 'SENTRA', 'TTN': 'TITAN', 'VSD': 'VERSA',
    'ARI': 'ARIYA',  'TXD': 'TITAN XD'}

@st.cache_data
def summarize_incoming_data(df, start_date, end_date, all_models, all_dealers):
    src = df.copy()
    src['ETA'] = pd.to_datetime(src['ETA'], errors='coerce').dt.normalize()

    # inclusive window for the passed month
    start = pd.Timestamp(start_date.year, start_date.month, 1)
    end   = pd.Timestamp(end_date.year, end_date.month, end_date.day)

    filtered = src[(src['ETA'] >= start) & (src['ETA'] <= end)]

    # exclude non-target dealers, then normalize names
    filtered = filtered[~filtered['DEALER_NAME'].str.upper().isin(["NISSAN OF BOONE", "EAST CHARLOTTE NISSAN"])]
    filtered['DEALER_NAME'] = filtered['DEALER_NAME'].replace(dealer_acronyms)

    # robust de-duplication
    filtered = add_unit_key(filtered)
    filtered.sort_values(['DEALER_NAME', 'UNIT_KEY', 'ETA'], inplace=True)
    filtered = filtered.drop_duplicates(subset=['DEALER_NAME','UNIT_KEY'], keep='last')

    # model labels to full names
    filtered = replace_mdl_with_full_name(filtered, reverse_mdl_mapping)

    combos = pd.MultiIndex.from_product([all_dealers, all_models], names=['DEALER_NAME','MDL'])
    summary = (filtered
        .groupby(['DEALER_NAME','MDL'])
        .size()
        .reindex(combos, fill_value=0)
        .reset_index(name='Count'))

    pivot = pd.pivot_table(
        summary,
        values='Count',
        index='MDL',
        columns='DEALER_NAME',
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Total'
    )
    return pivot

def summarize_retailed_data(df, start_date, end_date, all_models, all_dealers):
    df['SOLD'] = pd.to_datetime(df['SOLD'], errors='coerce')
    filtered_df = df[(df['LOC'] == 'RETAILED')]
    filtered_df = filtered_df[~filtered_df['DEALER_NAME'].str.upper().isin(["NISSAN OF BOONE", "EAST CHARLOTTE NISSAN"])]
    filtered_df['DEALER_NAME'] = filtered_df['DEALER_NAME'].replace(dealer_acronyms)
    filtered_df = replace_mdl_with_full_name(filtered_df, reverse_mdl_mapping)
    all_combinations = pd.MultiIndex.from_product([all_dealers, all_models], names=['DEALER_NAME', 'MDL'])
    summary = filtered_df.groupby(['DEALER_NAME', 'MDL']).size().reindex(all_combinations, fill_value=0).reset_index(name='Count')
    pivot_table = pd.pivot_table(summary, values='Count', index='MDL', columns='DEALER_NAME', aggfunc='sum', fill_value=0, margins=True, margins_name='Total')
    return pivot_table

def summarize_current_inventory(dataframes):
    combined_data = pd.concat(
        {store: df.set_index("Model")["Dlr Inventory"] for store, df in dataframes.items() if "Dlr Inventory" in df},
        axis=1,
    ).fillna(0)
    combined_data.columns = [dlr_acronyms.get(col, col) for col in combined_data.columns]
    combined_data.reset_index(inplace=True)
    combined_data = combined_data[~combined_data["Model"].isin(["GT-R", "TITAN XD"])]
    combined_data["Total"] = combined_data.iloc[:, 1:].sum(axis=1)
    total_row = combined_data.loc[combined_data["Model"].str.lower() == "total"]
    combined_data = combined_data[combined_data["Model"].str.lower() != "total"].sort_values("Model")
    if not total_row.empty:
        combined_data = pd.concat([combined_data, total_row], ignore_index=True)
    return combined_data

def summarize_dlv_date_data(df, start_date, end_date, all_models, all_dealers):
    df['DLV_DATE'] = pd.to_datetime(df['DLV_DATE'], errors='coerce')
    filtered_df = df[(df['DLV_DATE'] >= start_date) & (df['DLV_DATE'] <= end_date)]
    filtered_df = filtered_df[~filtered_df['DEALER_NAME'].str.upper().isin(["NISSAN OF BOONE", "EAST CHARLOTTE NISSAN"])]
    filtered_df['DEALER_NAME'] = filtered_df['DEALER_NAME'].replace(dealer_acronyms)
    filtered_df = replace_mdl_with_full_name(filtered_df, reverse_mdl_mapping)
    all_combinations = pd.MultiIndex.from_product([all_dealers, all_models], names=['DEALER_NAME', 'MDL'])
    summary = filtered_df.groupby(['DEALER_NAME', 'MDL']).size().reindex(all_combinations, fill_value=0).reset_index(name='Count')
    pivot_table = pd.pivot_table(summary, values='Count', index='MDL', columns='DEALER_NAME', aggfunc='sum', fill_value=0, margins=True, margins_name='Total')
    return pivot_table

def dataframe_to_html(df):
    html = df.to_html(classes='dataframe-container', border=0, index_names=False)
    return html
    
def dataframe_to_html_90(df):
    html = df.to_html(classes='dataframe-container', border=0, index=False)  # Set index=False
    return html

def reindex_table_to_match_models(df, models_to_match, index_col='MDL'):
    """Reindex a dataframe to include all models from models_to_match, filling missing with zeros."""
    if df.empty or not models_to_match:
        return df
    
    try:
        # Handle pivot tables with index (like incoming summaries)
        if index_col in df.index.names or (hasattr(df.index, 'name') and df.index.name == index_col):
            # Get current index values (excluding Total)
            current_index = [str(m) for m in df.index if str(m).upper() != 'TOTAL']
            # Create new index with models_to_match + Total if it existed
            new_index = models_to_match.copy()
            if 'Total' in df.index or any(str(m).upper() == 'TOTAL' for m in df.index):
                new_index.append('Total')
            
            # Reindex to include all models, filling missing with 0
            reindexed = df.reindex(new_index, fill_value=0)
            return reindexed
        
        # Handle dataframes with 'Model' column (like 90-day sales and current inventory)
        if 'Model' in df.columns:
            # Get current models (excluding Total)
            current_models = df[df['Model'].astype(str).str.upper() != 'TOTAL']['Model'].tolist()
            # Create list of all models to show
            all_models = models_to_match.copy()
            # Check if Total row exists
            has_total = any(df['Model'].astype(str).str.upper() == 'TOTAL')
            
            # Create a new dataframe with all models
            result_rows = []
            for model in all_models:
                # Find matching row (case-insensitive)
                matching = df[df['Model'].astype(str).str.upper() == str(model).upper()]
                if not matching.empty:
                    result_rows.append(matching.iloc[0].to_dict())
                else:
                    # Create zero row for missing model
                    zero_row = {col: 0 if col != 'Model' else model for col in df.columns}
                    result_rows.append(zero_row)
            
            # Add Total row if it existed
            if has_total:
                total_row = df[df['Model'].astype(str).str.upper() == 'TOTAL'].iloc[0].to_dict()
                result_rows.append(total_row)
            
            result_df = pd.DataFrame(result_rows)
            # Recalculate Total row if it exists
            if has_total and len(result_df) > 0:
                total_idx = result_df[result_df['Model'].astype(str).str.upper() == 'TOTAL'].index
                if len(total_idx) > 0:
                    numeric_cols = result_df.select_dtypes(include=[np.number]).columns
                    result_df.loc[total_idx[0], numeric_cols] = result_df[result_df['Model'].astype(str).str.upper() != 'TOTAL'][numeric_cols].sum()
            
            return result_df
        
    except Exception as e:
        # If reindexing fails, return original dataframe
        return df
    
    return df

with tab4:
    container = st.container()
    if not combined_data.empty:
        today = datetime.today()
        start_of_month = today.replace(day=1)
        next_month_start = start_of_month + relativedelta(months=1)
        following_month_start = start_of_month + relativedelta(months=2)
        start_for_calc = start_of_month + relativedelta(months=3)
        end_of_month = next_month_start - timedelta(days=1)
        next_month_end = following_month_start - timedelta(days=1)
        following_month_end = start_for_calc - timedelta(days=1)
        all_models = combined_data['MDL'].replace(reverse_mdl_mapping).unique()
        all_dealers = combined_data['DEALER_NAME'].replace(dealer_acronyms)
        all_dealers = all_dealers[~combined_data['DEALER_NAME'].str.upper().isin([d.upper() for d in excluded_dealers])].unique()
        with container:
            # Calculate balance_to_arrive first to get the models list
            current_month_summary = summarize_incoming_data(combined_data, start_of_month, end_of_month, all_models, all_dealers)
            current_month_dlv_summary = summarize_dlv_date_data(combined_data, start_of_month, end_of_month, all_models, all_dealers)
            balance_to_arrive = current_month_summary.subtract(current_month_dlv_summary, fill_value=0)
            
            # Get models from balance_to_arrive (excluding Total row)
            if not balance_to_arrive.empty:
                balance_models = [str(m) for m in balance_to_arrive.index if str(m).upper() != 'TOTAL']
            else:
                balance_models = []
            
            blank_col1, col1, col2, col3, blank_col2 = st.columns([0.1, 1, 1, 1, 0.1])
            with col1:
                
                st.markdown(f"<h5 style='text-align: center;'>Incoming for {start_of_month.strftime('%B')}</h5>", unsafe_allow_html=True)
                if balance_models:
                    current_month_summary_filtered = reindex_table_to_match_models(current_month_summary, balance_models, 'MDL')
                else:
                    current_month_summary_filtered = current_month_summary
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html(current_month_summary_filtered)}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<h5 style='text-align: center;'>90-Day Sales Summary</h5>", unsafe_allow_html=True)
                if balance_models:
                    formatted_90_day_sales_filtered = reindex_table_to_match_models(formatted_90_day_sales, balance_models, 'Model')
                else:
                    formatted_90_day_sales_filtered = formatted_90_day_sales
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html_90(formatted_90_day_sales_filtered)}</div>", unsafe_allow_html=True)
            
            with col2:
                next_month_summary = summarize_incoming_data(combined_data, next_month_start, next_month_end, all_models, all_dealers)
                current_inventory_summary = summarize_current_inventory(store_summaries)
                
                st.markdown(f"<h5 style='text-align: center;'>Incoming for {next_month_start.strftime('%B')}</h5>", unsafe_allow_html=True)
                if balance_models:
                    next_month_summary_filtered = reindex_table_to_match_models(next_month_summary, balance_models, 'MDL')
                else:
                    next_month_summary_filtered = next_month_summary
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html(next_month_summary_filtered)}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<h5 style='text-align: center;'>Current Inventory</h5>", unsafe_allow_html=True)
                if balance_models:
                    current_inventory_summary_filtered = reindex_table_to_match_models(current_inventory_summary, balance_models, 'Model')
                else:
                    current_inventory_summary_filtered = current_inventory_summary
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html_90(current_inventory_summary_filtered)}</div>", unsafe_allow_html=True)
            
            with col3:
                following_month_summary = summarize_incoming_data(combined_data, following_month_start, following_month_end, all_models, all_dealers)
                
                st.markdown(f"<h5 style='text-align: center;'>Incoming for {following_month_start.strftime('%B')}</h5>", unsafe_allow_html=True)
                if balance_models:
                    following_month_summary_filtered = reindex_table_to_match_models(following_month_summary, balance_models, 'MDL')
                else:
                    following_month_summary_filtered = following_month_summary
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html(following_month_summary_filtered)}</div>", unsafe_allow_html=True)
                
                st.markdown(f"<h5 style='text-align: center;'>Balance to Arrive for {start_of_month.strftime('%B')}</h5>", unsafe_allow_html=True)
                st.markdown(f"<div class='dataframe-container'>{dataframe_to_html(balance_to_arrive)}</div>", unsafe_allow_html=True)
    else:
        st.error("No data to display.")

def plot_metric(dataframes, metric, title, ylabel):
    fig = go.Figure()
    
    colors = ['#c3002f', '#8c8c8c', '#4d4d4d', '#d9d9d9']

    for i, (name, df) in enumerate(dataframes.items()):
        fig.add_trace(go.Bar(
            x=df['Model'],
            y=df[metric],
            name=name,
            marker=dict(color=colors[i])
        ))

    fig.update_layout(
        title=title,
        xaxis_title='Model',
        yaxis_title=ylabel,
        barmode='group',
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117',
        font=dict(color='#d0d0d0')
    )
    
    # Define configuration options
    config = {
        'displayModeBar': False,
        'staticPlot': False,
        'scrollZoom': True,
        'doubleClick': 'reset+autosize'
    }
    
    st.plotly_chart(fig, config=config)

with tab5:
    st.markdown("### 📊 Sales Analytics & Trends")
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
    
    # Load sales data with error handling
    dataframes = {}
    sales_files = {
        'Concord': 'files/Concord90.xls',
        'Hickory': 'files/Hickory90.xls',
        'Lake': 'files/Lake90.xls',
        'Winston': 'files/Winston90.xls'
    }
    
    for name, file_path in sales_files.items():
        try:
            if os.path.exists(file_path):
                dataframes[name] = process_excel(file_path)
            else:
                st.warning(f"⚠️ File not found: {file_path}")
        except Exception as e:
            st.warning(f"⚠️ Error processing {name}: {str(e)}")
    
    if not dataframes:
        st.error("❌ No sales data files found. Please upload the 90-day sales files.")
    
    bl1, col1, col2, bl2 = st.columns([0.1, 1, 1, 0.1])
    with col1:
        plot_metric(dataframes, 'Sold Roll 90', 'Sales Trends Over the Last 90 Days', 'Sold Roll 90')
        plot_metric(dataframes, 'Sold-MTD', 'Month-to-Date Sales Performance', 'Sold-MTD')
    
    with col2:
        plot_metric(dataframes, 'Days Supply', 'Inventory Levels (Days Supply)', 'Days Supply')
        plot_metric(dataframes, 'Dlr Inventory', 'Dealer Inventory Comparison', 'Dlr Inventory')
