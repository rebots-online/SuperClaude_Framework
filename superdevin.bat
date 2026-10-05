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

where devin >nul 2>&1 || goto :nocli
set /p ANSWER=Register context7 + sequential-thinking MCP servers via 'devin mcp add' (user scope)? [y/N] 
if /i "%ANSWER%"=="y" (
    devin mcp add context7 --scope user -- npx -y @upstash/context7-mcp@latest
    devin mcp add sequential-thinking --scope user -- npx -y @modelcontextprotocol/server-sequential-thinking
)
goto :tail
:nocli
echo (devin CLI not found - skipping optional MCP registration)
echo   To add later: devin mcp add context7 --scope user -- npx -y @upstash/context7-mcp@latest
echo                 devin mcp add sequential-thinking --scope user -- npx -y @modelcontextprotocol/server-sequential-thinking
:tail
echo.
echo Project scope instead: xcopy /E /I /Y "%SRC%\skills" ".devin\skills"
echo Restart Devin session (or /skills) for new entries to appear.
