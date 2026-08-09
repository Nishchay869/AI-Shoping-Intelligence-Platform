"""Scheduled job: alert shoppers via WhatsApp when a tracked receipt's warranty is expiring soon.

No scheduler exists in this backend - this script is the callable entry point. Wire it to an actual
scheduler to run daily, e.g. a system crontab entry:
    0 9 * * * cd /path/to/backend && .venv/bin/python -m scripts.send_warranty_alerts
or the equivalent scheduled-job feature on whatever platform this deploys to.

Usage (from backend/, with the venv active and a real Postgres configured):
    python -m scripts.send_warranty_alerts
"""
from app.db.session import SessionLocal
from app.services.warranty_alerts import send_expiring_warranty_alerts


def main() -> None:
    db = SessionLocal()
    try:
        notified = send_expiring_warranty_alerts(db)
        print(f"Sent {len(notified)} warranty-expiry alert(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
