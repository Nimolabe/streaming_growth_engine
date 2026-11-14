"""Kommandozeile des Setup-Agenten.

Beispiele:
  python -m setup_agent demo --out ../vorschau          # Beispieldaten lokal, ohne Datenbank
  python -m setup_agent run apply --out ../public-data   # Produktion (Firestore)
  python -m setup_agent run weekly
  python -m setup_agent set-admin --email admin@example.org
  python -m setup_agent status

Produktion braucht die Umgebungsvariable FIREBASE_SERVICE_ACCOUNT (Inhalt der Schlüsseldatei als JSON).
Optional: PRICE_FEEDS='[{"name": "partner-a", "url": "https://…"}]' für zulässige Preis-Feeds.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import repository as R
from .models import utcnow


def _firestore_repo():
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not raw:
        raise SystemExit("FIREBASE_SERVICE_ACCOUNT ist nicht gesetzt. Abbruch, nichts wurde geändert.")
    from .firestore_repo import FirestoreRepository

    return FirestoreRepository.from_service_account(raw)


def _price_sources(fetcher):
    from .monitors import JsonFeedPriceSource

    feeds = json.loads(os.environ.get("PRICE_FEEDS", "[]") or "[]")
    return [JsonFeedPriceSource(f["name"], path=f.get("path"), url=f.get("url"), fetcher=fetcher) for f in feeds]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="setup_agent", description="Setup Intelligence Agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="geplanten Job ausführen (Firestore)")
    run.add_argument("job", choices=["apply", "weekly", "prices", "export"])
    run.add_argument("--out", type=Path, help="Zielordner für den JSON-Export")

    demo = sub.add_parser("demo", help="Beispieldaten im Speicher erzeugen und exportieren (keine Datenbank)")
    demo.add_argument("--out", type=Path, required=True)

    admin = sub.add_parser("set-admin", help="Admin-Recht (Custom Claim) für ein Firebase-Konto setzen oder entziehen")
    who = admin.add_mutually_exclusive_group(required=True)
    who.add_argument("--uid")
    who.add_argument("--email")
    admin.add_argument("--remove", action="store_true")

    sub.add_parser("status", help="letzte Läufe und offene Vorschläge anzeigen")

    args = parser.parse_args(argv)

    if args.cmd == "demo":
        from . import exporter
        from .demo import seed

        repo = R.InMemoryRepository()
        now = utcnow()
        seed(repo, now)
        report = exporter.write(repo, args.out, now)
        print(f"Beispieldaten exportiert nach {args.out}: {len(report.written)} Dateien.")
        return 0

    if args.cmd == "set-admin":
        from firebase_admin import auth  # type: ignore[import-not-found]

        repo = _firestore_repo()  # initialisiert die Firebase-App
        import firebase_admin  # type: ignore[import-not-found]

        app = firebase_admin.get_app("setup-agent")
        user = auth.get_user(args.uid, app=app) if args.uid else auth.get_user_by_email(args.email, app=app)
        claims = dict(user.custom_claims or {})
        if args.remove:
            claims.pop("admin", None)
        else:
            claims["admin"] = True
        auth.set_custom_user_claims(user.uid, claims, app=app)
        print(f"Admin-Recht {'entzogen' if args.remove else 'gesetzt'} für {user.uid}. Gilt nach erneutem Anmelden.")
        del repo
        return 0

    repo = _firestore_repo()

    if args.cmd == "status":
        from .models import ProposalStatus

        print(json.dumps(repo.get_meta("agent"), indent=2, ensure_ascii=False))
        print(f"Offene Vorschläge: {len(repo.list_proposals(ProposalStatus.PENDING))}")
        return 0

    from .fetcher import HttpFetcher
    from .jobs import run_job

    fetcher = HttpFetcher()
    result = run_job(args.job, repo, out_dir=args.out, fetcher=fetcher, price_sources=_price_sources(fetcher))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
