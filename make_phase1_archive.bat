@echo off
rem Builds CSAI301_PacMan_Phase1.zip (video + report + code + contribution statement).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0make_submission_archive.ps1" -Phase 1
echo.
pause
