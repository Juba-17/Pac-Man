@echo off
rem Builds CSAI301_PacMan_Phase2.zip (video + report + code + contribution statement).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0make_submission_archive.ps1" -Phase 2
echo.
pause
