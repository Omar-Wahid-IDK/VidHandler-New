@echo off
echo ========================================================
echo Building VidHandler.exe using embedded Python Runtime...
echo ========================================================

:: Run PyInstaller using your embedded portable Python
Runtime\python.exe -m PyInstaller --onefile --noconsole --collect-all customtkinter --name "VidHandler" Scripts\Gui\Gui.py

echo.
echo Moving VidHandler.exe to the root project folder...
if exist dist\VidHandler.exe (
    move /y dist\VidHandler.exe .
)

echo.
echo Cleaning up build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist VidHandler.spec del VidHandler.spec

echo.
echo ========================================================
echo Build complete! VidHandler.exe is ready in the root folder.
echo ========================================================
pause