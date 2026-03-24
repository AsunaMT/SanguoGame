cd E:\sanguo-game\sanguo-game
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload 2>&1 | Out-File -FilePath server.log -Encoding utf8 -Append
