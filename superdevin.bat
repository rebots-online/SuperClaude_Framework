@echo off
REM superdevin.bat - install SuperClaude port for Devin CLI / Windsurf
setlocal
set SRC=%~dp0devin
set DST=%APPDATA%\devin\skills

if not exist "%SRC%\skills" (echo rendered skills missing: %SRC%\skills & exit /b 1)

echo Copying skills to %DST%
xcopy /E /I /Y "%SRC%\skills" "%DST%" >nul
xcopy /E /I /Y "%SRC%\superclaude-import" "%DST%\superclaude-import" >nul
echo Installed: 63 /sc-* skills + superclaude-import (/superclaude-import).

REM vendor plugin tree so imported bodies can resolve supporting files
xcopy /E /I /Y "%~dp0plugins\superclaude" "%APPDATA%\devin\superclaude\plugin" >nul
echo Vendored reference tree -^> %APPDATA%\devin\superclaude\plugin

echo.
echo Project scope instead: xcopy /E /I /Y "%SRC%\skills" ".devin\skills"
echo Restart Devin session (or /skills) for new entries to appear.
