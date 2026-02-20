# Responsible for selecting the correct AI model
"""
backend/model_dispatcher.py - AI Model Dispatcher
==================================================
Selects and invokes the correct AI model based on the
requested model_type. Keeps model selection decoupled
from controller and model implementation logic.
"""

import logging
from typing import Any, Dict

from config import SUPPORTED_MODEL_TYPES

logger = logging.getLogger(__name__)


class ModelDispatcher:
    """
    Routes an X-ray analysis request to the appropriate AI model.

    Adding a new model:
      1. Create models/<new_model>.py with a `predict(image_path)` function.
      2. Add its import inside `_build_registry()`.
      3. Register the model_type string in config.SUPPORTED_MODEL_TYPES.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Any] = self._build_registry()

    # ─────────────────────────────────────────────
    # REGISTRY BUILDER
    # ─────────────────────────────────────────────

    @staticmethod
    def _build_registry() -> Dict[str, Any]:
        """
        Lazily imports and registers all model modules.

        Returns:
            Dict mapping model_type string → model module.
        """
        registry: Dict[str, Any] = {}

        try:
            from models import bone_model
            registry["bone"] = bone_model
        except ImportError:
            logger.warning("bone_model not available — skipping registration.")

        try:
            from models import lung_model
            registry["lung"] = lung_model
        except ImportError:
            logger.warning("lung_model not available — skipping registration.")

        try:
            from models import disease_model
            registry["disease"] = disease_model
        except ImportError:
            logger.warning("disease_model not available — skipping registration.")

        logger.info(
            "ModelDispatcher registry built: %s", list(registry.keys())
        )
        return registry

    # ─────────────────────────────────────────────
    # PUBLIC DISPATCH METHOD
    # ─────────────────────────────────────────────

    def dispatch(self, model_type: str, image_path: str) -> Dict[str, Any]:
        """
        Selects the model for *model_type* and runs prediction.

        Args:
            model_type:  One of the SUPPORTED_MODEL_TYPES (e.g. 'bone').
            image_path:  File-system path to the uploaded X-ray image.

        Returns:
            Dict with at minimum:
                {
                    "model_type": str,
                    "image_path": str,
                    "finding":    str,
                    "confidence": float,
                    "raw":        Any   # full model output
                }

        Raises:
            ValueError: If model_type is not supported.
            RuntimeError: If the underlying model raises an error.
        """
        model_type = model_type.strip().lower()

        if model_type not in SUPPORTED_MODEL_TYPES:
            raise ValueError(
                f"Unsupported model_type '{model_type}'. "
                f"Supported: {SUPPORTED_MODEL_TYPES}"
            )

        model_module = self._registry.get(model_type)

        if model_module is None:
            raise RuntimeError(
                f"Model '{model_type}' is registered as supported but its "
                "module could not be loaded. Check import errors above."
            )

        logger.info(
            "Dispatching — model_type=%s  image=%s", model_type, image_path
        )

        try:
            raw_result = model_module.predict(image_path)
        except Exception as exc:                   # noqa: BLE001
            logger.error(
                "Model '%s' raised an error for image '%s': %s",
                model_type, image_path, exc,
            )
            raise RuntimeError(
                f"Model '{model_type}' prediction failed: {exc}"
            ) from exc

        return self._normalise_result(model_type, image_path, raw_result)

    # ─────────────────────────────────────────────
    # RESULT NORMALISATION
    # ─────────────────────────────────────────────

    @staticmethod
    def _normalise_result(
        model_type: str,
        image_path: str,
        raw: Any,
    ) -> Dict[str, Any]:
        """
        Converts raw model output into a standard response shape.

        Args:
            model_type: The model that produced the result.
            image_path: The image that was analysed.
            raw:        The direct return value from model.predict().

        Returns:
            Normalised dict ready for storage and API response.
        """
        if isinstance(raw, dict):
            return {
                "model_type": model_type,
                "image_path": image_path,
                "finding":    raw.get("finding",    "No finding provided."),
                "confidence": float(raw.get("confidence", 0.0)),
                "raw":        raw,
            }

        # Fallback: raw is a plain string
        return {
            "model_type": model_type,
            "image_path": image_path,
            "finding":    str(raw),
            "confidence": 0.0,
            "raw":        raw,
        }

    # ─────────────────────────────────────────────
    # UTILITIES
    # ─────────────────────────────────────────────

    def available_models(self) -> list:
        """Returns a list of currently loaded model types."""
        return list(self._registry.keys())
