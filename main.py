import pandas as pd
import streamlit as st
import os

st.set_page_config(layout="wide")
file_paths = [
    'files/VinpipeReport.xls',
    'files/VinpipeReport (1).xls',
    'files/VinpipeReport (2).xls',
    'files/VinpipeReport (3).xls'
]
def load_data(file_paths):
    data_frames = []
    for file in file_paths:
        try:
            if os.path.exists(file):
                dfs = pd.read_html(file)
                df = dfs[0] if dfs else None
                if df is not None:
                    data_frames.append(df)
            else:
                st.error(f"File {file} not found in the repository.")
        except Exception as e:
            st.error(f"Error loading {file}: {e}")
    return data_frames
data_frames = load_data(file_paths)
if data_frames:
    combined_data = pd.concat(data_frames, ignore_index=True)
else:
    combined_data = pd.DataFrame()
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Concord", "Winston", "Lake", "Hickory", "All Stores"])
if data_frames:
    with tab1:
        st.write("### Concord Inventory")
        st.dataframe(data_frames[0], use_container_width=True, height=780)
    with tab2:
        st.write("### Winston Inventory")
        st.dataframe(data_frames[1], use_container_width=True, height=780)
    with tab3:
        st.write("### Lake Inventory")
        st.dataframe(data_frames[2], use_container_width=True, height=780)
    with tab4:
        st.write("### Hickory Inventory")
        st.dataframe(data_frames[3], use_container_width=True, height=780)
if not combined_data.empty:
    with tab5:
        st.write("### Group Inventory")
        st.dataframe(combined_data, use_container_width=True, height=780)
else:
    st.error("No data to display.")
