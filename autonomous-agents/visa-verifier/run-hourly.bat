@echo off
REM ================================================================
REM run-hourly.bat — fires once per hourly scheduled-task tick.
REM
REM Only runs during the overnight window (22:00 - 07:00 local time).
REM Outside that window, exits silently without consuming quota.
REM
REM To change the overnight window: edit the `if` line below.
REM To change per-run capacity:     edit the --limit value below.
REM To stop the whole schedule:     schtasks /Delete /TN VisaVerifierHourly /F
REM ================================================================

cd /d "%~dp0"

REM Parse current hour (handles leading-zero "09" → 9 correctly).
set H=1%time:~0,2%
set /a HOUR=%H% - 100

REM Overnight window: 22:00-06:59 local. During the day we bail fast.
REM (All-day override that was active 2026-04-26 → 2026-04-28 has been
REM  reverted; back to overnight-only mode.)
set "LOG=output\hourly-%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%.log"
if %HOUR% geq 7 if %HOUR% lss 22 (
  echo %DATE% %TIME%  skip ^(hour=%HOUR% outside 22-07 overnight window^) >> "%LOG%"
  exit /b 0
)

echo. >> "%LOG%"
echo ======== %DATE% %TIME%  hour=%HOUR% ======== >> "%LOG%"

REM --limit is sized for Claude Max daily quota. Lower to 30 if you see frequent quota bails.
python agent.py --limit 50 --parallel 4 --sync >> "%LOG%" 2>&1

echo -- exit %ERRORLEVEL% -- >> "%LOG%"
exit /b %ERRORLEVEL%
