param(
  [string]$Python = "",
  [string[]]$PytestArgs = @("backend/tests", "-q"),
  [string]$DatabaseUrl = "sqlite:///./test-review.db",
  [switch]$KeepServer
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $Python) {
  $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
  if (Test-Path $venvPython) {
    $Python = $venvPython
  } else {
    $Python = "python"
  }
}

function Test-ApiReady {
  try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8002/health" -Method Get -TimeoutSec 2
    return $response.status -eq "healthy"
  } catch {
    return $false
  }
}

$startedServer = $false
$serverProcess = $null

if (-not (Test-ApiReady)) {
  Write-Host "Starting API server on 127.0.0.1:8002..."
  $env:RATE_LIMIT_ENABLED = "false"
  $env:DATABASE_URL = $DatabaseUrl

  $serverProcess = Start-Process -FilePath $Python -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8002") -WorkingDirectory (Join-Path $repoRoot "backend") -PassThru

  $startedServer = $true

  $attempts = 0
  while (-not (Test-ApiReady)) {
    Start-Sleep -Milliseconds 500
    $attempts++
    if ($attempts -ge 60) {
      throw "API server did not become ready within 30 seconds."
    }
  }
  Write-Host "API server is ready."
} else {
  Write-Host "Using existing API server on 127.0.0.1:8002."
}

try {
  Write-Host "Running pytest $($PytestArgs -join ' ')"
  Push-Location $repoRoot
  & $Python -m pytest @PytestArgs
  $testExitCode = $LASTEXITCODE
  Pop-Location
  exit $testExitCode
} finally {
  if ($startedServer -and -not $KeepServer -and $serverProcess) {
    Write-Host "Stopping API server (PID $($serverProcess.Id))..."
    Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
  }
}
