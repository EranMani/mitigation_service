@echo off
echo ===================================================
echo   MITIGATION SERVICE - STARTUP (Windows)
echo ===================================================

echo.
echo [1/3] CHECKING FOR PORT CONFLICTS... [cite: 42]
FOR /f "tokens=*" %%i IN ('docker ps -q --filter "publish=8000"') DO (
    echo Found old container %%i blocking port 8000. Stopping it... [cite: 43]
    docker rm -f %%i [cite: 43]
)

echo.
echo [2/3] CLEANING UP RESOURCES... [cite: 44]
docker compose down 2>nul [cite: 44]

echo.
echo [3/3] STARTING SERVICE... [cite: 45]
echo Note: If this is your first time, ensure you have internet.
echo If already built, this will start instantly offline.
echo.
docker compose up

pause