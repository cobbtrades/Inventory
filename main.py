import os
import pandas as pd
import streamlit as st
import gdown

# Google Drive shared folder link and file IDs
shared_folder_link = "https://drive.google.com/drive/folders/1ZiLHDNPFmzmqICqze5ar4tm2T2y41VdD?usp=sharing"
file_names = ["VinpipeReport.xls", "VinpipeReport.xls (1)", "VinpipeReport.xls (2)", "VinpipeReport.xls (3)"]

def download_files_from_drive(shared_link, file_names):
    folder_id = shared_link.split('/')[-1].split('?')[0]
    base_url = f"https://drive.google.com/uc?export=download&id="
    files = []
    for file_name in file_names:
        file_id = get_file_id(folder_id, file_name)
        if file_id:
            gdown.download(base_url + file_id, file_name, quiet=False)
            files.append(pd.read_excel(file_name))
    return files

def get_file_id(folder_id, file_name):
    url = f"https://drive.google.com/drive/u/0/folders/{folder_id}"
    response = requests.get(url)
    if response.status_code == 200:
        for line in response.text.splitlines():
            if file_name in line:
                file_id = line.split('"')[1].split("data-id=")[-1]
                return file_id
    return None

st.set_page_config(page_title="Inventory Dashboard", layout="wide")

# Download and load the data
files = download_files_from_drive(shared_folder_link, file_names)
data_frames = [pd.read_excel(file) for file in files]

# Combine all data into one DataFrame
combined_data = pd.concat(data_frames)

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["CN", "WS", "LN", "HK", "All Stores"])

with tab1:
    st.write("### Concord Inventory")
    st.dataframe(data_frames[0])

with tab2:
    st.write("### Winston Inventory")
    st.dataframe(data_frames[1])

with tab3:
    st.write("### Lake Inventory")
    st.dataframe(data_frames[2])

with tab4:
    st.write("### Hickory Inventory")
    st.dataframe(data_frames[3])

with tab5:
    st.write("### Group Inventory")
    st.dataframe(combined_data)
