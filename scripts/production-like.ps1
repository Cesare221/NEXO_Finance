# Production-like rehearsal wrapper
# Usage: .\scripts\production-like.ps1 <command>
# Commands: Up, Down, Migrate, Smoke

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Up", "Down", "Migrate", "Smoke")]
    [string]$Command,
    [switch]$RemoveData
)

$ComposeFile = "docker-compose.production-like.yml"

switch ($Command) {
    "Up" {
        if (-not (Test-Path ".env.production-like")) {
            if (Test-Path ".env.production-like.example") {
                Write-Host "Creating .env.production-like from example..." -ForegroundColor Yellow
                Copy-Item ".env.production-like.example" ".env.production-like"
            } else {
                Write-Host "ERROR: No .env.production-like or .env.production-like.example found" -ForegroundColor Red
                exit 1
            }
        }
        Write-Host "Starting production-like stack..." -ForegroundColor Cyan
        docker compose -f $ComposeFile up --build -d
        Write-Host "Stack started. API: http://localhost:8000 | Web: http://localhost:3011" -ForegroundColor Green
    }
    "Down" {
        if ($RemoveData) {
            Write-Host "Stopping and removing volumes..." -ForegroundColor Yellow
            docker compose -f $ComposeFile down -v
        } else {
            Write-Host "Stopping stack (preserving volumes)..." -ForegroundColor Yellow
            docker compose -f $ComposeFile down
        }
    }
    "Migrate" {
        Write-Host "Running migrations..." -ForegroundColor Cyan
        docker compose -f $ComposeFile run --rm migrate
    }
    "Smoke" {
        Write-Host "Running smoke tests..." -ForegroundColor Cyan
        python apps/api/scripts/smoke_production.py --web-url http://localhost:3011 --api-url http://localhost:8000 --allow-http-localhost
    }
}
