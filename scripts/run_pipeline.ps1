# Run the full due diligence pipeline (Windows)
# Usage: .\scripts\run_pipeline.ps1 "Tesla" [standard|quick|deep]

param(
    [Parameter(Mandatory=$true)]
    [string]$Company,

    [string]$Depth = "standard"
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$safeName = $Company -replace '\s+', '_'
$Output = "artifacts\reports\${safeName}_${timestamp}.md"

Write-Host "============================================="
Write-Host "  Due Diligence Agent"
Write-Host "  Company: $Company"
Write-Host "  Depth: $Depth"
Write-Host "  Output: $Output"
Write-Host "============================================="

# Load .env if present
if (-not $env:GOOGLE_API_KEY -and (Test-Path ".env")) {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim().Trim('"')
            [Environment]::SetEnvironmentVariable($key, $val, "Process")
        }
    }
}

if (-not $env:GOOGLE_API_KEY) {
    Write-Host "ERROR: GOOGLE_API_KEY not set. Get one at https://aistudio.google.com/apikey" -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force -Path "artifacts\reports" | Out-Null

python main.py --company "$Company" --depth $Depth --output "$Output"

Write-Host ""
Write-Host "Report saved to: $Output"
