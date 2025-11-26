@echo off
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
python -c "import pandas, geopandas, streamlit; print('Instalacion correcta')"