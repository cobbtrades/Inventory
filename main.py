import pandas as pd
import streamlit as st
import os
from bs4 import BeautifulSoup

# Define the file paths
file_paths = [
    'VinpipeReport.xls',
    'VinpipeReport (1).xls',
    'VinpipeReport (2).xls',
    'VinpipeReport (3).xls'
]

# Function to check if content is HTML
def is_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read(1024)
    return '<html' in content.lower()

# Function to load data from HTML file
def load_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    tables = soup.find_all('table')
    df = pd.read_html(str(tables))[0]  # Assuming the first table is the desired one
    return df

# Function to load data from files
def load_data(file_paths):
    data_frames = []
    for file in file_paths:
        try:
            if os.path.exists(file):
                if is_html(file):
                    df = load_html(file)
                else:
                    df = pd.read_excel(file)
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
    combined_data = pd.concat(data_frames)
else:
    combined_data = pd.DataFrame()

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

if not combined_data.empty:
    with tab5:
        st.write("### Combined Inventory")
        st.dataframe(combined_data)
else:
    st.error("No data to display.")
