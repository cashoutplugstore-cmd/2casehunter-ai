# Local test

From Termux:

```bash
cd ~/2casehunter-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd apps/worker
bash run_local.sh
```

Then test in another Termux session:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","service":"worker"}
```

No provider API keys are required for the local queue-only mode.
