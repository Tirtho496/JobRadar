$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop is required. Install it from https://www.docker.com/products/docker-desktop/ and run this file again."
}
& cmd.exe /d /c "docker info >nul 2>nul"
if ($LASTEXITCODE -ne 0) { throw "Docker Desktop is installed but the Docker engine is not running." }
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
docker compose up --build -d
Write-Host ""
Write-Host "JobRadar is running at http://localhost:8080" -ForegroundColor Green
Write-Host "The first scan starts automatically. The first semantic-ranking run may download a free local model."
Write-Host "To inspect backend logs: docker compose logs -f backend"
