<<<<<<< HEAD
@echo off
echo Building GBrowser v5.4...
echo.

echo Step 1: Installing dependencies...
pip install PyQt6 PyQt6-WebEngine pywin32 pyinstaller
if errorlevel 1 goto error

echo.
echo Step 2: Building executable with PyInstaller...
pyinstaller --noconfirm --onedir --windowed --name "GBrowser" --icon "GBrowser.ico" --add-data "blocklist.txt;." GBrowser.py
if errorlevel 1 goto error

echo.
echo Step 3: Copying assets to dist...
copy /Y blocklist.txt dist\GBrowser\
copy /Y GBrowser.ico dist\GBrowser\

echo.
echo Step 4: Building installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" GBrowser.iss
if errorlevel 1 goto error

echo.
echo Build complete!
echo Output: releases\5.4\GBrowser-5.4-Setup.exe
goto end

:error
echo.
echo BUILD FAILED!
exit /b 1

:end
=======
@echo off
echo Building GBrowser v5.4...
echo.

echo Step 1: Installing dependencies...
pip install PyQt6 PyQt6-WebEngine pywin32 pyinstaller
if errorlevel 1 goto error

echo.
echo Step 2: Building executable with PyInstaller...
pyinstaller --noconfirm --onedir --windowed --name "GBrowser" --icon "GBrowser.ico" --add-data "blocklist.txt;." GBrowser.py
if errorlevel 1 goto error

echo.
echo Step 3: Copying assets to dist...
copy /Y blocklist.txt dist\GBrowser\
copy /Y GBrowser.ico dist\GBrowser\

echo.
echo Step 4: Building installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" GBrowser.iss
if errorlevel 1 goto error

echo.
echo Build complete!
echo Output: releases\5.4\GBrowser-5.4-Setup.exe
goto end

:error
echo.
echo BUILD FAILED!
exit /b 1

:end
>>>>>>> 3a4b9cd6867348c7b13f21fcb4f6ba890a39c090
