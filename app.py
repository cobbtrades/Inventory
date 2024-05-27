import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Function to load data from Google Drive
def load_data(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("YourInventorySpreadsheet").worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Streamlit App
st.title("Inventory Management")

tabs = ["Store 1", "Store 2", "Store 3", "Store 4", "All Stores"]
tab = st.sidebar.selectbox("Select Store", tabs)

if tab == "Store 1":
    df = load_data("Store1")
    st.dataframe(df)
elif tab == "Store 2":
    df = load_data("Store2")
    st.dataframe(df)
elif tab == "Store 3":
    df = load_data("Store3")
    st.dataframe(df)
elif tab == "Store 4":
    df = load_data("Store4")
    st.dataframe(df)
elif tab == "All Stores":
    df1 = load_data("Store1")
    df2 = load_data("Store2")
    df3 = load_data("Store3")
    df4 = load_data("Store4")
    df_all = pd.concat([df1, df2, df3, df4], ignore_index=True)
    st.dataframe(df_all)
