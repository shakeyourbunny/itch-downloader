@echo off
if exist __pycache__ rmdir /q /s __pycache__
if exist build rmdir /q /s build
if exist dist rmdir /q /s dist

if exist itch-downloader.exe del itch-downloader.exe

pyinstaller --onefile itch-downloader.py

if exist dist\itch-downloader.exe move dist\itch-downloader.exe .
if exist dist rmdir /q /s dist
pause
