$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root "backend")
pip install -r requirements.txt
# app.py 기준으로 실행합니다. (Swagger: http://127.0.0.1:8000/docs)
python -m uvicorn app:app --reload --port 8000
