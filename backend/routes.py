# API routes will be defined here
"""
backend/routes.py - API Route Registration
==========================================
Defines all backend API endpoints and maps them to controller functions.
Keeps routing logic completely separate from business logic.

Designed to be framework-agnostic at this layer.  The `register_routes()`
function is called by app.py.  When integrating with a framework such as
Flask or FastAPI, swap the stub router below for the real one.
"""

import logging
from typing import Callable, Dict

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# FRAMEWORK-AGNOSTIC ROUTE TABLE
# ─────────────────────────────────────────────

class SimpleRouter:
    """
    Lightweight route registry used until a real HTTP framework is wired in.

    Stores route definitions so they can be inspected or handed off to Flask,
    FastAPI, or any other framework that register_routes() might wrap.
    """

    def __init__(self) -> None:
        self._routes: Dict[str, Dict] = {}

    def add(self, path: str, method: str, handler: Callable, **meta) -> None:
        """
        Registers a route.

        Args:
            path:    URL path (e.g. '/api/analyse').
            method:  HTTP method string ('GET', 'POST', …).
            handler: Controller function to call.
            **meta:  Optional metadata (description, tags, etc.).
        """
        key = f"{method.upper()} {path}"
        self._routes[key] = {
            "path":    path,
            "method":  method.upper(),
            "handler": handler,
            **meta,
        }
        logger.debug("Route registered → %s %s", method.upper(), path)

    def list_routes(self) -> list:
        """Returns all registered routes as a list of dicts."""
        return list(self._routes.values())


_router = SimpleRouter()


# ─────────────────────────────────────────────
# ROUTE DEFINITIONS
# ─────────────────────────────────────────────

def _define_routes() -> None:
    """
    Maps each URL + HTTP method to its controller function.
    Import controllers here to keep them out of module-level scope.
    """
    from backend.controller import (
        analyse_xray,
        get_patient_result,
        list_all_patients,
    )
    from chatbot.chatbot_engine import ChatbotEngine

    chatbot = ChatbotEngine()

    # ── X-ray Analysis ──────────────────────────────
    _router.add(
        path="/api/analyse",
        method="POST",
        handler=analyse_xray,
        description="Upload an X-ray image and receive an AI analysis result.",
        tags=["analysis"],
    )

    # ── Patient Data ─────────────────────────────────
    _router.add(
        path="/api/patients",
        method="GET",
        handler=list_all_patients,
        description="List all patient analysis records.",
        tags=["patients"],
    )

    _router.add(
        path="/api/patients/<patient_id>",
        method="GET",
        handler=get_patient_result,
        description="Fetch a single patient record by ID.",
        tags=["patients"],
    )

    # ── Chatbot ───────────────────────────────────────
    _router.add(
        path="/api/chatbot",
        method="POST",
        handler=chatbot.handle_query,
        description="Send a doctor query to the chatbot engine.",
        tags=["chatbot"],
    )


# ─────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────

def register_routes() -> SimpleRouter:
    """
    Registers all application routes and returns the router.

    Called by app.py at startup.  When integrating with Flask/FastAPI,
    pass the framework app object here and bind _router entries to it.

    Returns:
        Populated SimpleRouter instance.
    """
    _define_routes()

    registered = _router.list_routes()
    logger.info("%d route(s) registered:", len(registered))
    for route in registered:
        logger.info("  [%s]  %s  →  %s()",
                    route["method"], route["path"], route["handler"].__name__)

    return _router


def get_router() -> SimpleRouter:
    """Returns the shared router instance (after register_routes() is called)."""
    return _router
