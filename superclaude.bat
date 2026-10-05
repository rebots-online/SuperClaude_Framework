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
xcopy /E /I /Y "%SRC%\mcp"      "%DST%" >nul
echo Installed: commands-^>commands\sc (/sc:*), agents, skills, modes+core+mcp docs.
echo.

where claude >nul 2>&1 || goto :nocli
set /p ANSWER=Register context7 + sequential-thinking MCP servers via 'claude mcp add'? [y/N] 
if /i "%ANSWER%"=="y" (
    claude mcp add context7 -- npx -y @upstash/context7-mcp@latest
    claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
)
goto :tail
:nocli
echo (claude CLI not found - skipping optional MCP registration)
echo   To add later: claude mcp add context7 -- npx -y @upstash/context7-mcp@latest
echo                 claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
:tail
echo Hooks (opt-in): merge %SRC%\hooks\hooks.json into ~/.claude/settings.json "hooks" section.
echo Restart Claude Code to pick up /sc:* commands.
