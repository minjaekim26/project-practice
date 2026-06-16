$ErrorActionPreference = "Stop"
$log = "C:\Users\selen\Projects\push-log.txt"
$proj = "C:\Users\selen\Projects\project-practice"
$local = "C:\Users\selen\Projects\project-practice-local"

function Log($m) {
    $line = "$(Get-Date -Format 'HH:mm:ss') $m"
    Write-Host $line
    Add-Content -Path $log -Value $line
}

Remove-Item $log -ErrorAction SilentlyContinue
Log "=== project-practice push start ==="

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Log "ERROR: git not found. Install Git for Windows first."
    exit 1
}

if (-not (Test-Path (Join-Path $proj ".git"))) {
    Log "No .git found. Preparing clone..."
    if (Test-Path $proj) {
        if (Test-Path $local) { Remove-Item $local -Recurse -Force }
        Move-Item $proj $local -Force
        Log "Backed up to project-practice-local"
    }
    git clone https://github.com/minjaekim26/project-practice.git $proj
    Log "Cloned repository"
    robocopy $local $proj /E /XD .git | Out-Null
    Log "Copied implementation files"
}

Set-Location $proj
git status
git add .
git commit -m "Add minimal music recommendation system (FastAPI + React)"
git pull --rebase origin main
git push -u origin main
Log "=== push complete ==="
