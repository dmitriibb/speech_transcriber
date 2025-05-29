@echo off
echo Cleaning up previous builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /f /q *.spec 2>nul
echo Cleanup complete! 