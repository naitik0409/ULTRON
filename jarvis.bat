@echo off
set "ULTRON_ROOT=C:\Users\naiti\Desktop\Ultron\ULTRON"
set "PYTHONPATH=%ULTRON_ROOT%;%PYTHONPATH%"
set "PYTHONUNBUFFERED=1"
python -u Main.py %*
