import pandas as pd
import streamlit as st
import os
import requests

# Set page configuration
st.set_page_config(layout="wide")

# Define file paths
file_paths = ['files/Concord', 'files/Winston', 'files/Lake', 'files/Hickory']

# Function to rename .xls files to .html and load data
def rename_and_load_data(file_paths):
    data_frames = []
    for file in file_paths:
        if os.path.exists(file):
            new_file = file.replace('.xls', '.html')
            os.rename(file, new_file)
            dfs = pd.read_html(new_file)
            df = dfs[0] if dfs else None
            df = df[['LOC_DESC','DLRORD','MDL','MDLYR','MCODE','VIN','OPTS','GOPTS','EXT','INT','DEALER_NAME','TRM_LVL','DRV_TRN','DLRETA','ORD_CUST_NAME','ORD_CUST_EMAIL_ADDR','ORD_CUST_DATE','DLR_DLV_DT']]
            if df is not None:
                data_frames.append((df, new_file))
        else:
            st.error(f"File {file} not found in the repository.")
    return data_frames

# Load data
data_frames = rename_and_load_data(file_paths)

# Combine data
if data_frames:
    combined_data = pd.concat([df[0] for df in data_frames], ignore_index=True)
else:
    combined_data = pd.DataFrame()

# Custom CSS for padding and container width
st.write(
    """
    <style>
    .main .block-container {
        padding-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Concord", "Winston", "Lake", "Hickory", "All Stores"])

# Function to save edited data back to GitHub
def save_to_github(file_path, data_frame, token):
    html_data = data_frame.to_html(index=False)
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
        "content": html_data.encode("utf-8").decode("utf-8"),
        "sha": sha
    }
    
    # Update the file on GitHub
    update_response = requests.put(url, headers=headers, json=payload)
    if update_response.status_code == 200:
        st.success(f"Successfully updated {file_path} on GitHub.")
    else:
        st.error(f"Failed to update {file_path} on GitHub: {update_response.text}")

# Display individual store data
if data_frames:
    for i, (df, file_path) in enumerate(data_frames):
        tab = [tab1, tab2, tab3, tab4][i]
        with tab:
            st.write(f"### {['Concord', 'Winston', 'Lake', 'Hickory'][i]} Inventory")
            edited_df = st.data_editor(df, height=780)
            token = os.getenv('GITHUB_TOKEN')
            if token and not edited_df.equals(df):
                save_to_github(file_path, edited_df, token)

# Display combined data for all stores
if not combined_data.empty:
    with tab5:
        st.write("### Group Inventory")
        st.data_editor(combined_data, use_container_width=True, height=780)
else:
    st.error("No data to display.")
