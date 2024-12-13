@echo off
REM Specify where you unzipped FFmpeg
set "ffmpeg_dir=C:\ffmpeg"

REM Ensure the ffmpeg folder exists
if not exist "%ffmpeg_dir%" (
    echo FFmpeg directory not found at %ffmpeg_dir%.
    exit /b
)

REM Add FFmpeg to the PATH for the current session
setx PATH "%ffmpeg_dir%\bin;%PATH%"

echo FFmpeg has been added to the system PATH. Please restart any open command prompt windows.
pause
