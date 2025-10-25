@echo off
REM Build script wrapper for Windows
cd /d "%~dp0"
python _source\build.py %*
