@echo off
echo ========================================================
echo Deploying PulseCare Clinic System to Google Cloud Run...
echo ========================================================

REM Check if gcloud is installed
where gcloud >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Google Cloud SDK (gcloud) is not found in PATH.
    echo Please install the Google Cloud SDK from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

echo [1/2] Submitting build and deploying to Cloud Run...
gcloud run deploy pulsecare --source . --platform managed --region us-central1 --allow-unauthenticated --port 8080

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo [SUCCESS] PulseCare deployed successfully to Google Cloud Run!
    echo Check the URL provided above by gcloud.
    echo ========================================================
) else (
    echo.
    echo [ERROR] Deployment failed. Check the error log above.
)

pause
