# DARK Shop

A starter Flask + Supabase e‑commerce scaffold with Discord OAuth, license key redemption, and a pluggable AI endpoint.

Quick start
1) Create and activate a virtualenv

Windows (PowerShell):
```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt
```

2) Copy env template and edit
```powershell
copy .env.example .env
```

3) Run dev server
```powershell
python run.py
```

Visit http://127.0.0.1:5000

Notes
- Fill Supabase and Discord OAuth values in `.env` before using Supabase/Discord features.
- This is a scaffold: secure service-role keys and add RLS when deploying.
