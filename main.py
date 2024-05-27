import pandas as pd
import streamlit as st
import os
import requests

# Set page configuration
st.set_page_config(layout="wide")

# Define file paths
file_paths = [
    'files/Concord',
    'files/Winston',
    'files/Lake',
    'files/Hickory'
]

# Function to rename .xls files to .html and load data
def rename_and_load_data(file_paths):
    data_frames = []
    for file in file_paths:
        if os.path.exists(file):
            new_file = file.replace('.xls', '.html')
            os.rename(file, new_file)
            dfs = pd.read_html(new_file)
            df = dfs[0] if dfs else None
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

# Custom CSS for padding, container width, and table height
st.write(
    """
    <style>
    .main .block-container {
        padding-top: 1rem;
    }
    .dataframe-container {
        height: 780px;
        overflow-y: auto;
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
    repo = "cobbtrades/Inventory"  # replace with your repository
    path = file_path
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    
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
            edited_df = st.experimental_data_editor(df)
            save_button = st.button("Save Changes", key=f"save_{i}")
            if save_button:
                token = st.text_input("Enter your GitHub token", type="password", key=f"token_{i}")
                if token:
                    save_to_github(file_path, edited_df, token)

# Display combined data for all stores
if not combined_data.empty:
    with tab5:
        st.write("### Group Inventory")
        st.markdown(
            combined_data.to_html(index=False, classes="dataframe-container"),
            unsafe_allow_html=True
        )
else:
    st.error("No data to display.")
