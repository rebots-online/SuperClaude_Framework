@echo off
REM superclaude.bat - install SuperClaude for Claude Code (upstream target)
setlocal
set SRC=%~dp0plugins\superclaude
set DST=%USERPROFILE%\.claude

where superclaude >nul 2>&1
if %errorlevel%==0 (
    echo Using official installer: superclaude install
    superclaude install %*
    goto :done
)
where pipx >nul 2>&1
if %errorlevel%==0 (
    echo Installing via pipx, then superclaude install
    pipx install superclaude && superclaude install %*
    goto :done
)

echo superclaude CLI not found - falling back to direct copy into %DST%
if not exist "%SRC%" (echo plugin tree missing: %SRC% & exit /b 1)
xcopy /E /I /Y "%SRC%\commands" "%DST%\commands\sc" >nul
xcopy /E /I /Y "%SRC%\agents"   "%DST%\agents" >nul
xcopy /E /I /Y "%SRC%\skills"   "%DST%\skills" >nul
xcopy /E /I /Y "%SRC%\modes"    "%DST%" >nul
xcopy /E /I /Y "%SRC%\core"     "%DST%" >nul
echo Copied commands->commands\sc, agents, skills, modes+core docs to %DST%
echo Note: .mcp.json and hooks not wired - configure under Claude Code settings if wanted.
:done
echo Restart Claude Code to pick up /sc:* commands.
