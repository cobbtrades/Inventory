import pandas as pd
import streamlit as st
import os

# Define the file paths
file_paths = [
    'VinpipeReport',
    'VinpipeReport (1)',
    'VinpipeReport (2)',
    'VinpipeReport (3)'
]

# Function to load data from files
def load_data(file_paths):
    data_frames = []
    for file in file_paths:
        if os.path.exists(file):
            df = pd.read_excel(file)
            data_frames.append(df)
        else:
            st.error(f"File {file} not found in the repository.")
    return data_frames

# Load the data
data_frames = load_data(file_paths)

# Combine all data into one DataFrame
combined_data = pd.concat(data_frames) if data_frames else None

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Store 1", "Store 2", "Store 3", "Store 4", "All Stores"])

if data_frames:
    with tab1:
        st.write("### Store 1 Inventory")
        st.dataframe(data_frames[0])

    with tab2:
        st.write("### Store 2 Inventory")
        st.dataframe(data_frames[1])

    with tab3:
        st.write("### Store 3 Inventory")
        st.dataframe(data_frames[2])

    with tab4:
        st.write("### Store 4 Inventory")
        st.dataframe(data_frames[3])

    if combined_data is not None:
        with tab5:
            st.write("### Combined Inventory")
            st.dataframe(combined_data)
    else:
        st.error("No data to display.")
else:
    st.error("No data loaded. Please check the file paths and try again.")
