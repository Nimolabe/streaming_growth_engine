"""REST-API v1 mit FastAPI (dokumentiert unter /api/v1/docs).

Start lokal mit Beispieldaten:   SETUP_AGENT_DEMO=1 uvicorn --factory setup_agent.api:app_from_env
Start mit Firestore:             FIREBASE_SERVICE_ACCOUNT='…' uvicorn --factory setup_agent.api:app_from_env

Die Logik steckt in api_core.py; hier werden nur Routen, Parameter und Fehlerformat verdrahtet.
"""

import os
from datetime import datetime
from typing import Any, Literal

from fastapi import Body, FastAPI, Header, Query, Request  # type: ignore[import-not-found]
from fastapi.exceptions import RequestValidationError  # type: ignore[import-not-found]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]
from fastapi.responses import JSONResponse  # type: ignore[import-not-found]

from . import __version__
from . import repository as R
from .api_core import SetupApi, TokenVerifier

PREFIX = "/api/v1"
# Auf Modulebene, damit FastAPI die Typangabe beim Start auflösen kann
Kind = Literal["streamers", "products", "claims", "offers", "sources", "source-registry"]


def create_app(repo: R.Repository, verifier: TokenVerifier, *, allowed_origins: list[str] | None = None) -> FastAPI:
    api = SetupApi(repo, verifier)
    app = FastAPI(title="Setup Intelligence Agent API", version=__version__, docs_url=f"{PREFIX}/docs",
                  openapi_url=f"{PREFIX}/openapi.json", redoc_url=None)
    if allowed_origins:
        app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["GET", "POST", "PATCH", "PUT"],
                           allow_headers=["Authorization", "Content-Type"])

    @app.exception_handler(RequestValidationError)
    async def _invalid(_: Request, exc: RequestValidationError):
        return JSONResponse(status_code=400, content={"error": {"code": "invalid_input", "message": "Ungültige Anfrage.",
                                                                "details": {"errors": exc.errors()[:5]}}})

    def respond(fn, *args, **kwargs) -> Any:
        status, body = api.call(fn, *args, **kwargs)
        return body if status == 200 else JSONResponse(status_code=status, content=body)

    Auth = Header(default=None, alias="Authorization")

    # ---------------- öffentlich
    @app.get(f"{PREFIX}/streamers", tags=["öffentlich"])
    def list_streamers(category: str | None = None, platform: str | None = None, language: str | None = None,
                       q: str | None = None, page: int = 1, page_size: int = 50):
        return respond(api.list_streamers, category=category, platform=platform, language=language, q=q, page=page, page_size=page_size)

    @app.get(f"{PREFIX}/streamers/{{streamer_id}}", tags=["öffentlich"])
    def get_streamer(streamer_id: str):
        return respond(api.streamer, streamer_id)

    @app.get(f"{PREFIX}/streamers/{{streamer_id}}/setup", tags=["öffentlich"])
    def get_setup(streamer_id: str, category: str | None = None):
        return respond(api.setup, streamer_id, category)

    @app.get(f"{PREFIX}/products", tags=["öffentlich"])
    def list_products(category: str | None = None, min_price: int | None = Query(None, ge=0),
                      max_price: int | None = Query(None, ge=0), currency: str = "EUR", q: str | None = None):
        return respond(api.list_products, category=category, min_price=min_price, max_price=max_price, currency=currency, q=q)

    @app.get(f"{PREFIX}/products/{{product_id}}", tags=["öffentlich"])
    def get_product(product_id: str):
        return respond(api.product, product_id)

    @app.get(f"{PREFIX}/products/{{product_id}}/offers", tags=["öffentlich"])
    def get_offers(product_id: str):
        return respond(api.offers, product_id)

    @app.get(f"{PREFIX}/products/{{product_id}}/alternatives", tags=["öffentlich"])
    def get_alternatives(product_id: str, max_price: int | None = Query(None, ge=0), limit: int = 5):
        return respond(api.alternatives, product_id, max_price=max_price, limit=limit)

    @app.get(f"{PREFIX}/meta", tags=["öffentlich"])
    def meta():
        return respond(api.meta)

    # ---------------- Admin
    @app.post(f"{PREFIX}/admin/{{kind}}", tags=["admin"])
    def admin_create(kind: Kind, body: dict = Body(...), authorization: str | None = Auth):
        return respond(api.admin_create, authorization, kind, body)

    @app.patch(f"{PREFIX}/admin/{{kind}}/{{entity_id}}", tags=["admin"])
    def admin_update(kind: Kind, entity_id: str, body: dict = Body(...), authorization: str | None = Auth):
        return respond(api.admin_update, authorization, kind, entity_id, body)

    @app.post(f"{PREFIX}/admin/{{kind}}/{{entity_id}}/retire", tags=["admin"])
    def admin_retire(kind: Kind, entity_id: str, body: dict = Body(...), authorization: str | None = Auth):
        return respond(api.admin_update, authorization, kind, entity_id, body, retire=True)

    @app.put(f"{PREFIX}/admin/offers/{{offer_id}}/price", tags=["admin"])
    def admin_price(offer_id: str, body: dict = Body(...), authorization: str | None = Auth):
        return respond(api.admin_set_price, authorization, offer_id, body)

    @app.get(f"{PREFIX}/admin/proposals", tags=["admin"])
    def admin_proposals(status: str | None = "pending", entity_type: str | None = None, authorization: str | None = Auth):
        return respond(api.admin_proposals, authorization, status=status, entity_type=entity_type)

    @app.post(f"{PREFIX}/admin/proposals/{{proposal_id}}/approve", tags=["admin"])
    def approve(proposal_id: str, body: dict = Body(default={}), authorization: str | None = Auth):
        return respond(api.admin_decide, authorization, proposal_id, True, (body or {}).get("note"))

    @app.post(f"{PREFIX}/admin/proposals/{{proposal_id}}/reject", tags=["admin"])
    def reject(proposal_id: str, body: dict = Body(...), authorization: str | None = Auth):
        return respond(api.admin_decide, authorization, proposal_id, False, (body or {}).get("note"))

    @app.get(f"{PREFIX}/admin/sources", tags=["admin"])
    def admin_sources(authorization: str | None = Auth):
        return respond(api.admin_sources, authorization)

    @app.get(f"{PREFIX}/admin/audit", tags=["admin"])
    def admin_audit(entity_type: str | None = None, entity_id: str | None = None, since: datetime | None = None,
                    authorization: str | None = Auth):
        return respond(api.admin_audit, authorization, entity_type=entity_type, entity_id=entity_id, since=since)

    return app


def app_from_env() -> FastAPI:
    origins = [o for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o]
    if os.environ.get("SETUP_AGENT_DEMO") == "1":
        from .demo import seed
        from .models import utcnow

        repo = R.InMemoryRepository()
        seed(repo, utcnow())

        class _NoAdmin:
            def verify(self, token: str) -> dict:
                raise PermissionError("Im Demo-Modus gibt es keine Admin-Anmeldung.")

        return create_app(repo, _NoAdmin(), allowed_origins=origins)

    from .api_core import FirebaseTokenVerifier
    from .cli import _firestore_repo

    repo = _firestore_repo()
    import firebase_admin  # type: ignore[import-not-found]

    return create_app(repo, FirebaseTokenVerifier(firebase_admin.get_app("setup-agent")), allowed_origins=origins)
