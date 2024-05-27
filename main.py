import pandas as pd
import streamlit as st
import os
from st_aggrid import AgGrid, GridOptionsBuilder
from github import Github
import base64

# Set page configuration to wide mode
st.set_page_config(layout="wide")

# Define the file paths
file_paths = [
    'VinpipeReport.xls',
    'VinpipeReport (1).xls',
    'VinpipeReport (2).xls',
    'VinpipeReport (3).xls'
]

# Function to load data from HTML files
def load_data(file_paths):
    data_frames = []
    for file in file_paths:
        try:
            if os.path.exists(file):
                # Read HTML content as a DataFrame
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    dfs = pd.read_html(content)
                    # Assuming the first table in the HTML is the relevant data
                    df = dfs[0] if dfs else None
                    if df is not None:
                        data_frames.append(df)
            else:
                st.error(f"File {file} not found in the repository.")
        except Exception as e:
            st.error(f"Error loading {file}: {e}")
    return data_frames

# Function to save data to files and update GitHub repo
def save_data_to_github(data_frames, file_paths):
    # Authenticate to GitHub
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo("your-username/your-repo-name")  # Replace with your username and repo name

    for df, file_path in zip(data_frames, file_paths):
        try:
            # Convert DataFrame to HTML and get binary content
            html_content = df.to_html(index=False)
            encoded_content = base64.b64encode(html_content.encode()).decode()

            # Get the file from the repo
            contents = repo.get_contents(file_path)
            # Update the file in the repo
            repo.update_file(contents.path, f"Update {file_path}", encoded_content, contents.sha)
        except Exception as e:
            st.error(f"Error saving {file_path} to GitHub: {e}")

# Load the data
data_frames = load_data(file_paths)

# Combine all data into one DataFrame if data is available
if data_frames:
    combined_data = pd.concat(data_frames)
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Store 1", "Store 2", "Store 3", "Store 4", "All Stores"])

# Editable dataframes using st_aggrid
def editable_dataframe(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True)
    grid_options = gb.build()
    grid_response = AgGrid(df, gridOptions=grid_options, editable=True, height=600, width='100%')
    return grid_response['data']

if data_frames:
    with tab1:
        st.write("### Store 1 Inventory")
        data_frames[0] = editable_dataframe(data_frames[0])

    with tab2:
        st.write("### Store 2 Inventory")
        data_frames[1] = editable_dataframe(data_frames[1])

    with tab3:
        st.write("### Store 3 Inventory")
        data_frames[2] = editable_dataframe(data_frames[2])

    with tab4:
        st.write("### Store 4 Inventory")
        data_frames[3] = editable_dataframe(data_frames[3])

if not combined_data.empty:
    with tab5:
        st.write("### Combined Inventory")
        combined_data = editable_dataframe(combined_data)

# Save changes button
if st.button("Save Changes"):
    save_data_to_github(data_frames, file_paths)
    st.success("Changes saved to GitHub.")
