@echo off
title PulseCare Clinic & Emergency System
echo ========================================================
echo Starting PulseCare Local Server...
echo ========================================================

start "" "http://localhost:5000"
python app.py

pause
