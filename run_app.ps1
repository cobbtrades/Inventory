# PowerShell script to run the app with virtual environment

Write-Host "Creating virtual environment (if it doesn't exist)..." -ForegroundColor Cyan
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "Virtual environment created!" -ForegroundColor Green
}

Write-Host "`nActivating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

Write-Host "`nInstalling/Updating dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "`nStarting Streamlit app..." -ForegroundColor Cyan
streamlit run main.py
