"""

Audit logging middleware.

Every time someone calls any of end points,  audit_logs table should record it automatically — who did what, when, which endpoint.

CONCEPTS DEMONSTRATED:
    - FastAPI middleware
    - Request/response lifecycle
    - Automatic audit trail
"""

import logging
import time
from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import Session

from database.Connection import SessionLocal
from database.Models import AuditLog

logger = logging.getLogger("oncotrack.middleware.audit")

# Endpoints we don't need to log
SKIP_PATHS = [
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
]


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Logs every API request to the audit_logs table.

    Records:
        - which endpoint was called
        - HTTP method (GET/POST/PATCH/DELETE)
        - response status code
        - how long it took
        - user info (if available from request headers)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip logging for non-API paths
        if any(request.url.path.startswith(path) for path in SKIP_PATHS):
            return await call_next(request)

        # -- Before route runs --------------------------------
        start_time = time.time()

        # Try to get username from request headers
        # In a real JWT system we'd decode the token here
        # For our demo we read it from a custom header
        username = request.headers.get("X-Username", "anonymous")

        # -- Run the actual route -----------------------------
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(f"Request failed: {e}")
            status_code = 500
            raise
        finally:
            # -- After route runs -----------------------------
            duration_ms = (time.time() - start_time) * 1000

            # Determine resource from URL path
            # e.g. /api/patients/1 → "patients"
            resource = _extract_resource(request.url.path)

            # Determine action from HTTP method
            action = _method_to_action(request.method)

            # Log to console
            logger.info(
                f"{action:<7} {request.url.path:<40} "
                f"{status_code} ({duration_ms:.1f}ms) "
                f"user={username}"
            )

            # Write to audit_logs table
            _write_audit_log(
                path        = str(request.url.path),
                action      = action,
                resource    = resource,
                status_code = status_code,
                username    = username,
                duration_ms = duration_ms,
            )

        return response


def _extract_resource(path: str) -> str:
    """
    Extracts resource name from URL path.

    Examples:
        /api/patients/1     → patients
        /api/labs/patient/1 → labs
        /auth/login         → auth
        /health             → system
    """
    parts = [p for p in path.split("/") if p]  # remove empty strings
    if not parts:
        return "system"
    if parts[0] == "api" and len(parts) > 1:
        return parts[1]   # api/patients/1 → patients
    return parts[0]       # auth/login → auth


def _method_to_action(method: str) -> str:
    """
    Maps HTTP method to action name for audit log.

    GET    → READ
    POST   → CREATE
    PATCH  → UPDATE
    DELETE → DELETE
    """
    mapping = {
        "GET"    : "READ",
        "POST"   : "CREATE",
        "PATCH"  : "UPDATE",
        "DELETE" : "DELETE",
        "PUT"    : "UPDATE",
    }
    return mapping.get(method.upper(), method)


def _write_audit_log(
    path        : str,
    action      : str,
    resource    : str,
    status_code : int,
    username    : str,
    duration_ms : float,
):
    """
    Writes one audit log entry to the database.
    Uses its own db session — separate from the request session.
    """
    db: Session = SessionLocal()
    try:
        log = AuditLog(
            action      = action,
            resource    = resource,
            endpoint    = path,
            status_code = status_code,
            # detail      = {
            #     "username"    : username,
            #     "duration_ms" : round(duration_ms, 1),
            # }
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
        db.rollback()
    finally:
        db.close()