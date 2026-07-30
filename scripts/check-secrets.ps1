# Secret scan — checks tracked files for leaked credentials
# Usage: pwsh scripts/check-secrets.ps1

$patterns = @(
    "gsk_[A-Za-z0-9]{20,}",
    "re_[A-Za-z0-9]{20,}",
    "sntrys_[A-Za-z0-9]{20,}",
    "sk-[A-Za-z0-9]{20,}",
    "Bearer [A-Za-z0-9\-._~+/]{20,}=*",
    "-----BEGIN (RSA |EC )?PRIVATE KEY-----"
)

$trackedFiles = git ls-files
$found = $false

foreach ($file in $trackedFiles) {
    if (-not (Test-Path $file)) { continue }
    $content = Get-Content $file -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }

    foreach ($pattern in $patterns) {
        if ($content -match $pattern) {
            Write-Host "LEAK: $file matches $pattern" -ForegroundColor Red
            $found = $true
        }
    }
}

if ($found) {
    Write-Host "`nSecrets detected in tracked files!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "No secrets found in tracked files." -ForegroundColor Green
}
