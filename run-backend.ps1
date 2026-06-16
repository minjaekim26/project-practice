$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root "backend")
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
