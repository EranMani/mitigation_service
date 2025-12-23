@echo off
echo ===================================================
echo   MITIGATION SERVICE - AUTOMATED STARTUP
echo ===================================================

echo.
echo [1/3] CHECKING FOR PORT 8000 CONFLICTS...

:: This command asks Docker: "Give me the ID of any container using port 8000"
:: If it finds one, it kills ONLY that container.
FOR /f "tokens=*" %%i IN ('docker ps -q --filter "publish=8000"') DO (
    echo Found old container %%i blocking port 8000. Stopping it...
    docker rm -f %%i
)

echo.
echo [2/3] CLEANING UP PROJECT RESOURCES...
:: Clean up only THIS project's containers
docker compose down 2>nul

echo.
echo [3/3] BUILDING AND STARTING...
docker compose up --build

pause