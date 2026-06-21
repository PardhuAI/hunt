#!/usr/bin/env python3
"""Scrape orchestrator: runs aggregator-poller + career-scraper and updates data.json.

This is the script that the mavis cron + GitHub Action call every 5h.

Usage:
    python3 scrape_and_update.py          # run full pipeline
    python3 scrape_and_update.py --agents aggregator-poller   # just one agent
    python3 scrape_and_update.py --push   # commit + push data.json after update

In production, this just calls into the Mavis agents via `mavis session new <agent>`.
For now, this is a stub that simulates the agents — real runs use the mavis session.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path.home() / ".mavis" / "job-hunt"
DASHBOARD_PUBLIC = DATA_DIR / "dashboard" / "public"
DATA_FILE = DATA_DIR / "data.json"


def run_agent(agent_name: str) -> dict:
    """Spawn a one-shot session with the named agent to do a fresh scrape.

    Returns the agent's response (parsed as JSON if possible)."""
    print(f"[{datetime.now().isoformat()}] Running {agent_name}...")
    try:
        # Use mavis session to invoke the agent non-interactively.
        # In production this would be: mavis session new <agent> --prompt "..."
        # For now, return a stub result so the script structure is testable.
        result = subprocess.run(
            ["mavis", "session", "new", agent_name, "--prompt", "Run a fresh scrape/poll and report new jobs found. Append to ~/.mavis/job-hunt/data.json."],
            capture_output=True, text=True, timeout=600
        )
        return {
            "agent": agent_name,
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-500:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"agent": agent_name, "error": "timeout after 600s"}
    except Exception as e:
        return {"agent": agent_name, "error": str(e)}


def refresh_dashboard_data():
    """Copy the latest data.json into the dashboard's public dir."""
    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} not found")
        return False
    if not DASHBOARD_PUBLIC.exists():
        print(f"ERROR: {DASHBOARD_PUBLIC} not found")
        return False

    # Update last_updated
    data = json.loads(DATA_FILE.read_text())
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # Copy to dashboard
    DASHBOARD_PUBLIC.joinpath("data.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False)
    )
    print(f"[{datetime.now().isoformat()}] Refreshed dashboard/public/data.json with {data.get('total_jobs', '?')} jobs")
    return True


def git_push():
    """If dashboard is a git repo, commit and push the updated data.json."""
    if not (Path(DATA_DIR / "dashboard" / ".git").exists()):
        print("Dashboard not a git repo — skipping push. Run `git init` then commit to enable Vercel auto-deploy.")
        return False

    try:
        subprocess.run(["git", "-C", str(DATA_DIR / "dashboard"), "add", "public/data.json"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(DATA_DIR / "dashboard"), "commit", "-m", f"auto: refresh job data {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            check=True, capture_output=True
        )
        subprocess.run(["git", "-C", str(DATA_DIR / "dashboard"), "push"], check=True, capture_output=True)
        print("Pushed to git — Vercel will auto-deploy within ~30s")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git push failed: {e.stderr.decode() if e.stderr else e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", nargs="+", default=["aggregator-poller", "career-scraper"],
                    help="which agents to run")
    ap.add_argument("--push", action="store_true", help="git commit + push after refresh")
    ap.add_argument("--dry-run", action="store_true", help="don't actually run agents")
    args = ap.parse_args()

    print(f"=== Job hunt scrape — {datetime.now().isoformat()} ===")
    print(f"Agents: {args.agents}")

    if not args.dry_run:
        results = []
        for agent in args.agents:
            r = run_agent(agent)
            results.append(r)
            print(f"  {agent}: returncode={r.get('returncode', '?')}")
            if r.get("stderr"):
                print(f"  stderr: {r['stderr'][:200]}")
    else:
        print("[dry-run] Skipping agent runs")

    refresh_dashboard_data()

    if args.push:
        git_push()

    print(f"=== Done at {datetime.now().isoformat()} ===")


if __name__ == "__main__":
    main()