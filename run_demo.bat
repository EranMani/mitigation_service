@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo      MITIGATION SERVICE - DEMO MODE
echo ===================================================

echo.
echo [1/3] STOPPING OLD CONTAINERS...
docker compose down 2>nul
FOR /f "tokens=*" %%i IN ('docker ps -q --filter "publish=8000"') DO docker rm -f %%i >nul 2>&1

echo.
echo [2/3] STARTING SERVER (In a new window)...
echo Check the other window for server logs!
:: "start" opens a new CMD window just for the server
start "Mitigation Server Logs" cmd /k "docker compose up --build"

echo.
echo [3/3] WAITING FOR SERVER TO WAKE UP (10 seconds)...
timeout /t 10 /nobreak >nul

echo.
echo ===================================================
echo            STARTING TEST BARRAGE
echo ===================================================
echo.
:: --- TEST 1: Safe Prompt ---
echo [TEST 1] Safe Greeting
curl -s -X POST http://localhost:8000/mitigate -d "{\"prompt\": \"Hello world, this is a safe message.\", \"user_id\": \"test_01\"}"
echo.
echo.

:: --- TEST 2: Email Redaction ---
echo [TEST 2] Email Leak
curl -s -X POST http://localhost:8000/mitigate -d "{\"prompt\": \"Contact me at elon@tesla.com please.\", \"user_id\": \"test_02\"}"
echo.
echo.

:: --- TEST 3: Phone Redaction ---
echo [TEST 3] Phone Leak
curl -s -X POST http://localhost:8000/mitigate -d "{\"prompt\": \"My number is 555-123-4567 call me.\", \"user_id\": \"test_03\"}"
echo.
echo.

:: --- TEST 4: Blocked Keyword (Kill) ---
echo [TEST 4] Violence (Blocked)
curl -s -X POST http://localhost:8000/mitigate -d "{\"prompt\": \"I want to kill the process.\", \"user_id\": \"test_04\"}"
echo.
echo.

:: --- TEST 5: Blocked Keyword (Hate) ---
echo [TEST 5] Hate Speech (Blocked)
curl -s -X POST http://localhost:8000/mitigate -d "{\"prompt\": \"I hate this assignment.\", \"user_id\": \"test_05\"}"
echo.
echo.

:: --- TEST 6: Multiple PII ---
echo [TEST 6] Combo (Email + Phone)
curl -s -X POST http://localhost:8000/mitigate -d "{\"prompt\": \"Email: bob@mail.com, Phone: 050-1234567\", \"user_id\": \"test_06\"}"
echo.
echo.

:: --- TEST 7: Secret Key ---
echo [TEST 7] API Secret Leak
curl -s -X POST http://localhost:8000/mitigate -d "{\"prompt\": \"My API key is SECRET{xyz_123}\", \"user_id\": \"test_07\"}"
echo.
echo.

:: --- TEST 8: Credit Card ---
echo [TEST 8] Credit Card Leak
curl -s -X POST http://localhost:8000/mitigate -d "{\"prompt\": \"Charge my card 1234 5678 1234 5678 now.\", \"user_id\": \"test_08\"}"
echo.
echo.

:: --- TEST 9: Mixed Case Block ---
echo [TEST 9] Mixed Case Evasion (KiLL)
curl -s -X POST http://localhost:8000/mitigate -d "{\"prompt\": \"Please KiLL the connection.\", \"user_id\": \"test_09\"}"
echo.
echo.

:: --- TEST 10: History Check ---
echo [TEST 10] Checking Audit Log (Last 20 items)
curl -s http://localhost:8000/history
echo.
echo.

:: --- TEST 11: Dynamic History ---
echo [TEST 11] Now Checking Audit Log (Last 4 items)
:: IMPORTANT: Use quotes "..." around URLs with special characters like ? or &
curl -s "http://localhost:8000/history?n=4"
echo.
echo.

:: --- TEST 12: BONUS ICAP ADAPTER ---
echo [TEST 12] BONUS: Testing ICAP Endpoint (Port 1344)
echo.
echo (A) Sending SAFE Request via TCP...
python -c "import socket; s=socket.socket(); s.connect(('localhost', 1344)); s.sendall(b'REQMOD icap://server/mitigate PROMPT=Hello ICAP World\n'); print('Response:', s.recv(1024).decode())"
echo.
echo (B) Sending BLOCKED Request via TCP...
python -c "import socket; s=socket.socket(); s.connect(('localhost', 1344)); s.sendall(b'REQMOD icap://server/mitigate PROMPT=I want to kill the process\n'); print('Response:', s.recv(1024).decode())"
echo.
echo.

:: --- TEST 13: Final Verification ---
echo [TEST 13] Verifying ICAP Log Entry (Checking last 2 entries)
curl -s "http://localhost:8000/history?n=2"
echo.
echo.

echo ===================================================
echo               DEMO COMPLETE 
echo ===================================================
pause