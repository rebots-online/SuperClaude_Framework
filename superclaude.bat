@echo off
REM superclaude.bat - install SuperClaude for Claude Code from THIS clone
REM (no PyPI/pipx; copies the vendored plugins/superclaude tree)
REM If you prefer the official package instead: pipx install superclaude ^&^& superclaude install
setlocal
set SRC=%~dp0plugins\superclaude
set DST=%USERPROFILE%\.claude

if not exist "%SRC%\commands" (echo plugin tree missing: %SRC% & exit /b 1)

echo Copying components to %DST%
xcopy /E /I /Y "%SRC%\commands" "%DST%\commands\sc" >nul
xcopy /E /I /Y "%SRC%\agents"   "%DST%\agents" >nul
xcopy /E /I /Y "%SRC%\skills"   "%DST%\skills" >nul
xcopy /E /I /Y "%SRC%\modes"    "%DST%" >nul
xcopy /E /I /Y "%SRC%\core"     "%DST%" >nul
echo Installed: commands-^>commands\sc (/sc:*), agents, skills, modes+core docs.
echo.
echo Not wired (official installer handles these): .mcp.json, hooks, CLAUDE.md imports.
echo Configure under Claude Code settings if wanted.
echo Restart Claude Code to pick up /sc:* commands.
