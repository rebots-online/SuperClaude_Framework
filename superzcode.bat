@echo off
REM superzcode.bat - install SuperClaude port for ZCode (GLM-5.x)
setlocal
set SRC=%~dp0zcode\superclaude
set DST=%USERPROFILE%\.zcode

if not exist "%SRC%\commands" (echo rendered plugin missing: %SRC% & exit /b 1)

echo Copying components to %DST% (user scope)
xcopy /E /I /Y "%SRC%\commands" "%DST%\commands" >nul
xcopy /E /I /Y "%SRC%\skills"   "%DST%\skills" >nul
xcopy /E /I /Y "%SRC%\agents"   "%DST%\agents" >nul
echo Installed: 30 commands ^(/sc-*^), 13 skills ^($sc-*^), 19 subagents.

echo.
echo For hooks + MCP servers + one-click enable/disable, install as a plugin instead:
echo   ZCode -^> Settings -^> Plugins -^> Create -^> Add marketplace
echo   -^> rebots-online/SuperClaude_Framework  (or this local folder)
echo   -^> Install 'superclaude'
echo.
echo Restart ZCode (new task) to pick up components.
