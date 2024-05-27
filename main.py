import pandas as pd
import streamlit as st
import os

# Set page configuration to wide mode
st.set_page_config(layout="wide")

# Define the file paths
file_paths = [
    'VinpipeReport.xls',
    'VinpipeReport (1).xls',
    'VinpipeReport (2).xls',
    'VinpipeReport (3).xls'
]

# Function to load data from files
def load_data(file_paths):
    data_frames = []
    for file in file_paths:
        try:
            if os.path.exists(file):
                # Read HTML content as a DataFrame
                dfs = pd.read_html(file)
                # Assuming the first table in the HTML is the relevant data
                df = dfs[0] if dfs else None
                if df is not None:
                    data_frames.append(df)
            else:
                st.error(f"File {file} not found in the repository.")
        except Exception as e:
            st.error(f"Error loading {file}: {e}")
    return data_frames

# Load the data
data_frames = load_data(file_paths)

# Combine all data into one DataFrame if data is available
if data_frames:
    combined_data = pd.concat(data_frames, ignore_index=True)
else:
    combined_data = pd.DataFrame()

# Custom CSS to reduce space above tabs and make the table full width
st.write(
    """
    <style>
    .main .block-container {
        padding-top: 1rem;
    }
    .dataframe { width: 100% !important; }
    .element-container { width: 100% !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Concord", "Winston", "Lake", "Hickory", "All Stores"])

if data_frames:
    with tab1:
        st.write("### Concord Inventory")
        st.dataframe(data_frames[0], use_container_width=True, height=600)

    with tab2:
        st.write("### Winston Inventory")
        st.dataframe(data_frames[1], use_container_width=True, height=600)

    with tab3:
        st.write("### Lake Inventory")
        st.dataframe(data_frames[2], use_container_width=True, height=600)

    with tab4:
        st.write("### Hickory Inventory")
        st.dataframe(data_frames[3], use_container_width=True, height=600)

if not combined_data.empty:
    with tab5:
        st.write("### Group Inventory")
        st.dataframe(combined_data, use_container_width=True, height=600)
else:
    st.error("No data to display.")
