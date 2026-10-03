"""Unified, passive Virelai semantic-library compiler.

The package has no Duck-facing surface.  It compiles immutable Ring 8 observations into a
single inspectable world model after play, so every claim can be graded before exposure.
"""

from inference.framework.virelai_semantic.compiler import (
    SEMANTIC_LIBRARY_SCHEMA,
    SemanticLibraryCompiler,
    compile_semantic_library,
)
from inference.framework.virelai_semantic.view import SemanticLibraryView
from inference.framework.virelai_semantic.depth_probe import ActivationObservation, LeverDepthPlanner
from inference.framework.virelai_semantic.depth_adapter import PointerDepthAdapter

__all__ = [
    "SEMANTIC_LIBRARY_SCHEMA",
    "SemanticLibraryCompiler",
    "compile_semantic_library",
    "SemanticLibraryView",
    "ActivationObservation",
    "LeverDepthPlanner",
    "PointerDepthAdapter",
]
