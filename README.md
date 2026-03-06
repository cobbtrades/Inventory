# 🚗 Modern Nissan Inventory Management

A modern, web-based inventory management system for Nissan dealerships with drag-and-drop file upload capabilities.

## 🚀 Quick Start

### Option 1: Using the Batch File (Windows)
Simply double-click `run_app.bat` to:
- Create a virtual environment (if needed)
- Install dependencies locally
- Start the app

### Option 2: Manual Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - **Windows (PowerShell):**
     ```bash
     venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```bash
     venv\Scripts\activate.bat
     ```
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Streamlit app:**
   ```bash
   streamlit run main.py
   ```

5. **Open your browser:**
   The app will automatically open in your default browser at `http://localhost:8501`

### Deactivating the Virtual Environment
When you're done, you can deactivate the virtual environment:
```bash
deactivate
```

## 📁 File Structure

- `main.py` - Main application file
- `files/` - Directory for inventory Excel files
- `InventoryUpdate.xlsx` - Current inventory file (in root directory)
- `requirements.txt` - Python dependencies

## 📤 Uploading Files

1. Click the "📁 Upload Files" section at the top of the app
2. Drag and drop your Excel files or click to browse
3. Supported files:
   - `Concord.xls`, `Winston.xls`, `Lake.xls`, `Hickory.xls`
   - `Concord90.xls`, `Hickory90.xls`, `Lake90.xls`, `Winston90.xls`
   - `InventoryUpdate.xlsx`
4. Click "💾 Save Files & Refresh Data" to update

## 🎯 Features

- **All Stores Inventory** - View and filter inventory across all locations
- **Current CDK Inventory** - Current inventory with metrics
- **Dealer Trade** - Generate trade PDFs
- **Incoming** - Incoming inventory analysis and sales summaries
- **Sales** - Sales analytics and trends with interactive charts

## 🔧 Requirements

- Python 3.8 or higher
- All dependencies listed in `requirements.txt`

## 💡 Tips

- The app automatically refreshes when you upload new files
- Use the filters in the "All Stores" tab to narrow down your search
- All data is cached for performance - cache clears automatically on file upload
