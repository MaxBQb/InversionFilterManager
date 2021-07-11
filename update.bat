@echo off
echo DO NOT RUN THIS SCRIPT BY YOURSELF
IF "%1"=="" exit
IF "%2"=="" exit
echo Final updating stage started
cd ..
echo Current version located in %1
echo Updated one is in %2
echo Backup file: "%1_old.zip"
timeout /t 5 /nobreak
rmdir /S /Q %1
rename %2 %1
cd %1
start main.exe
call :deleteSelf&exit /b
:deleteSelf
start /b "" cmd /c del "%~f0"&exit /b