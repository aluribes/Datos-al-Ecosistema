#!/bin/bash

pip3 install --upgrade pip
pip3 install -r requirements.txt
python -c "import pandas, geopandas, streamlit; print('Instalacion correcta')"