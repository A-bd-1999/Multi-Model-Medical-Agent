"""
app.py - Medical Multi-Model AI Agent — Application Entry Point
===============================================================
Initializes and wires together all core system components:
  - Database connection health check
  - Backend route registration
  - Chatbot engine readiness

Run with:
    python app.py
"""

import logging
import sys
from database.db_connection import DatabaseConnection
from config import PROJECT_NAME, PROJECT_VERSION, DEBUG, DB_CONFIG

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# COMPONENT IMPORTS (deferred to catch import errors cleanly)
# ─────────────────────────────────────────────
def _import_components():
    """
    Lazily import all subsystem modules.
    Returns a dict of component references or raises on failure.
    """
    try:
        from database.db_connection import DatabaseConnection
        from chatbot.chatbot_engine import ChatbotEngine
        from backend.routes import register_routes
        return {
            "DatabaseConnection": DatabaseConnection,
            "ChatbotEngine":      ChatbotEngine,
            "register_routes":    register_routes,
        }
    except ImportError as exc:
        logger.critical("Failed to import core components: %s", exc)
        raise


# ─────────────────────────────────────────────
# INITIALISATION STEPS
# ─────────────────────────────────────────────
def _check_database(DatabaseConnection) -> bool:
    """
    Verifies that the database is reachable at startup.

    Args:
        DatabaseConnection: The DB connection class.

    Returns:
        True if healthy, False otherwise.
    """
    logger.info("Checking database connectivity …")
    try:
        db = DatabaseConnection()
        conn = db.get_connection()
        if conn and conn.is_connected():
            conn.close()
            logger.info("✅  Database connection OK  (host=%s, db=%s)",
                        DB_CONFIG["host"], DB_CONFIG["database"])
            return True
        logger.warning("⚠️  Database connection returned a falsy handle.")
        return False
    except Exception as exc:          # noqa: BLE001
        logger.error("❌  Database unreachable: %s", exc)
        return False


def _init_chatbot(ChatbotEngine) -> object:
    """
    Instantiates the ChatbotEngine and confirms it is ready.

    Args:
        ChatbotEngine: The chatbot class.

    Returns:
        Initialised ChatbotEngine instance.
    """
    logger.info("Initialising Chatbot Engine …")
    engine = ChatbotEngine()
    logger.info("✅  Chatbot Engine ready.")
    return engine


def _register_backend_routes(register_routes) -> None:
    """
    Registers all backend API routes.

    Args:
        register_routes: Route-registration callable from backend.routes.
    """
    logger.info("Registering backend routes …")
    register_routes()
    logger.info("✅  Backend routes registered.")


# ─────────────────────────────────────────────
# MAIN APPLICATION BOOT
# ─────────────────────────────────────────────
def main() -> None:
    """
    Boots the Medical Multi-Model AI Agent system.

    Sequence:
      1. Import subsystem components.
      2. Verify database connectivity.
      3. Initialise the chatbot engine.
      4. Register API routes.
      5. Report ready status.
    """
    logger.info("=" * 60)
    logger.info("  %s  v%s", PROJECT_NAME, PROJECT_VERSION)
    logger.info("=" * 60)

    # 1. Import
    components = _import_components()

    # 2. Database check
    db_ok = _check_database(components["DatabaseConnection"])
    if not db_ok:
        logger.critical("Aborting startup — database is unavailable.")
        sys.exit(1)

    # 3. Chatbot
    _init_chatbot(components["ChatbotEngine"])

    # 4. Routes
    _register_backend_routes(components["register_routes"])

    # 5. Ready
    logger.info("=" * 60)
    logger.info("  System fully initialised. Ready to accept requests.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
