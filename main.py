import streamlit as st
import os
import base64
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import cups

# Define your Streamlit app layout and form
st.set_page_config(layout="wide")

# Custom CSS for styling
st.write(
    """
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to calculate transfer amount
def calculate_transfer_amount(key_charge, projected_cost):
    return projected_cost - key_charge

def format_currency(value):
    return "${:,.2f}".format(value)

# Function to create a PDF from form data
def create_pdf(data, filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica", 12)

    c.drawString(100, height - 40, f"Date: {data['date']}")
    c.drawString(100, height - 60, f"Manager: {data['manager']}")
    c.drawString(100, height - 100, "Dealer Trade Details:")
    c.drawString(100, height - 120, f"From: {data['from']}")
    c.drawString(100, height - 140, f"To: {data['to']}")
    c.drawString(100, height - 160, f"Stock Number: {data['stock_number']}")
    c.drawString(100, height - 180, f"Year Make Model: {data['year_make_model']}")
    c.drawString(100, height - 200, f"Full VIN: {data['full_vin']}")
    c.drawString(100, height - 220, f"Key Charge: {data['key_charge']}")
    c.drawString(100, height - 240, f"Projected Cost: {data['projected_cost']}")
    c.drawString(100, height - 260, f"Transfer Amount: {data['transfer_amount']}")
    
    c.drawString(100, height - 300, "Non-Modern Dealership Information:")
    c.drawString(100, height - 320, f"Dealership Name: {data['dealership_name']}")
    c.drawString(100, height - 340, f"Address: {data['address']}")
    c.drawString(100, height - 360, f"City, State ZIP: {data['city_state_zip']}")
    c.drawString(100, height - 380, f"Phone Number: {data['phone_number']}")
    c.drawString(100, height - 400, f"Dealer Code: {data['dealer_code']}")
    c.drawString(100, height - 420, f"Contact Name: {data['contact_name']}")

    c.drawString(100, height - 460, "Outgoing Unit:")
    c.drawString(100, height - 480, f"Outgoing Stock Number: {data['outgoing_stock_number']}")
    c.drawString(100, height - 500, f"Outgoing Year Make Model: {data['outgoing_year_make_model']}")
    c.drawString(100, height - 520, f"Outgoing Full VIN: {data['outgoing_full_vin']}")
    c.drawString(100, height - 540, f"Outgoing Sale Price: {data['outgoing_sale_price']}")

    c.drawString(100, height - 580, "Incoming Unit:")
    c.drawString(100, height - 600, f"Incoming Year Make Model: {data['incoming_year_make_model']}")
    c.drawString(100, height - 620, f"Incoming Full VIN: {data['incoming_full_vin']}")
    c.drawString(100, height - 640, f"Incoming Purchase Price: {data['incoming_purchase_price']}")

    c.save()

# Function to print PDF
def print_pdf(filename):
    conn = cups.Connection()
    printers = conn.getPrinters()
    default_printer = list(printers.keys())[0]
    conn.printFile(default_printer, filename, "Trade Document", {})

# Form for Dealer Trade
with st.form(key="dealer_trade_form"):
    col1, col2 = st.columns(2)
    with col1:
        current_date = datetime.today()
        formatted_date = current_date.strftime("%B %d, %Y")
        st.write(f"Date: {formatted_date}")
    with col2:
        manager = st.text_input("Manager", key="manager_input")

    col3, col4, col5 = st.columns([1, 1, 2])
    with col3:
        our_trade = st.checkbox("Our Trade", key="our_trade_checkbox")
        sold = st.checkbox("Sold", key="sold_checkbox")
    with col4:
        their_trade = st.checkbox("Their Trade", key="their_trade_checkbox")
        floorplan = st.checkbox("Floorplan", key="floorplan_checkbox")
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
        from_location = st.text_input("From:", key="from_input")
    with col7:
        to_location = st.text_input("To:", key="to_input")

    col8, col9 = st.columns(2)
    with col8:
        stock_number = st.text_input("Stock Number", key="stock_number_input")
        year_make_model = st.text_input("Year Make Model", key="year_make_model_input")
        full_vin = st.text_input("Full VIN #", key="full_vin_input")
    with col9:
        key_charge = st.number_input("Key Charge ($)", value=0.00, format="%.2f", key="key_charge_input")
        projected_cost = st.number_input("Projected Cost ($)", value=0.00, format="%.2f", key="projected_cost_input")
        transfer_amount = calculate_transfer_amount(key_charge, projected_cost)
        formatted_transfer_amount = format_currency(transfer_amount)
        st.text_input("Transfer Amount", value=formatted_transfer_amount, key="transfer_amount_input", disabled=True)

    st.text("Non-Modern Dealership Information")
    dealership_name = st.text_input("Dealership Name", key="dealership_name_input")
    address = st.text_input("Address", key="address_input")
    city_state_zip = st.text_input("City, State ZIP Code", key="city_state_zip_input")
    phone_number = st.text_input("Phone Number", key="phone_number_input")
    dealer_code = st.text_input("Dealer Code", key="dealer_code_input")
    contact_name = st.text_input("Contact Name", key="contact_name_input")

    st.text("Outgoing Unit")
    outgoing_stock_number = st.text_input("Outgoing Stock Number", key="outgoing_stock_number_input")
    outgoing_year_make_model = st.text_input("Outgoing Year Make Model", key="outgoing_year_make_model_input")
    outgoing_full_vin = st.text_input("Outgoing Full VIN #", key="outgoing_full_vin_input")
    outgoing_sale_price = st.text_input("Outgoing Sale Price", key="outgoing_sale_price_input")

    st.text("Incoming Unit")
    incoming_year_make_model = st.text_input("Incoming Year Make Model", key="incoming_year_make_model_input")
    incoming_full_vin = st.text_input("Incoming Full VIN #", key="incoming_full_vin_input")
    incoming_purchase_price = st.text_input("Incoming Purchase Price", key="incoming_purchase_price_input")

    if st.form_submit_button("Submit Trade"):
        data = {
            'date': formatted_date,
            'manager': manager,
            'our_trade': our_trade,
            'sold': sold,
            'their_trade': their_trade,
            'floorplan': floorplan,
            'from': from_location,
            'to': to_location,
            'stock_number': stock_number,
            'year_make_model': year_make_model,
            'full_vin': full_vin,
            'key_charge': key_charge,
            'projected_cost': projected_cost,
            'transfer_amount': formatted_transfer_amount,
            'dealership_name': dealership_name,
            'address': address,
            'city_state_zip': city_state_zip,
            'phone_number': phone_number,
            'dealer_code': dealer_code,
            'contact_name': contact_name,
            'outgoing_stock_number': outgoing_stock_number,
            'outgoing_year_make_model': outgoing_year_make_model,
            'outgoing_full_vin': outgoing_full_vin,
            'outgoing_sale_price': outgoing_sale_price,
            'incoming_year_make_model': incoming_year_make_model,
            'incoming_full_vin': incoming_full_vin,
            'incoming_purchase_price': incoming_purchase_price
        }

        # Create and print the PDF
        pdf_filename = "trade_document.pdf"
        create_pdf(data, pdf_filename)
        print_pdf(pdf_filename)
        st.success("Trade Submitted and Document Sent to Printer")
