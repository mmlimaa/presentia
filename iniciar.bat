@echo off
title Presentia
cd /d "%~dp0"
poetry run python manage.py runserver 8001
pause
