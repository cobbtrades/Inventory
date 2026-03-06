@echo off
echo Creating virtual environment (if it doesn't exist)...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created!
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing/Updating dependencies...
pip install -r requirements.txt

echo.
echo Starting Streamlit app...
streamlit run main.py

pause
