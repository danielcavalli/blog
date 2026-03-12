@echo off
REM Build script wrapper for Windows
cd /d "%~dp0"
uv run python _source\build.py %*
