@echo off
REM ================================================================
REM run-hourly.bat — fires once per hourly scheduled-task tick.
REM
REM Does a bounded verifier run (150 pairs, parallel=4). TTL-skip
REM means already-verified entries are left alone. Logs to output/.
REM
REM To change per-run capacity:  edit the --limit value below.
REM To change concurrency:        edit the --parallel value below.
REM To stop the whole schedule:   schtasks /Delete /TN VisaVerifierHourly /F
REM ================================================================

cd /d "%~dp0"

REM Use the user's normal python + claude CLI from PATH.
set "LOG=output\hourly-%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%.log"

echo. >> "%LOG%"
echo ======== %DATE% %TIME% ======== >> "%LOG%"

REM --limit is sized for Claude Max daily quota. Lower to 30 if you see frequent quota bails.
python agent.py --limit 50 --parallel 4 --sync >> "%LOG%" 2>&1

echo -- exit %ERRORLEVEL% -- >> "%LOG%"
exit /b %ERRORLEVEL%
