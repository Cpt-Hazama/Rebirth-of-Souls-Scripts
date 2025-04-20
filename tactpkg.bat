@echo off
setlocal enabledelayedexpansion
set SCRIPT=tactpkg.py

if "%~1"=="" (
    echo Drag .tactpkg files to extract animation labels.
    pause
    exit /b
)

for %%F in (%*) do (
    set "file=%%~fF"
    if /i "%%~xF"==".tactpkg" (
        echo Processing: !file!
        py "!SCRIPT!" "!file!"
    )
)

echo.
echo Done!
pause