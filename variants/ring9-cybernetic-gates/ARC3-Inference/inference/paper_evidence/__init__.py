"""The paper-evidence layer (WO-PE-03B/C/D): atomic claims, answer keys and the five-category grader.

Author: Claude (Alpha build seat), 2026-10-25. Base ``0f2e703``. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25``.

Offline only (Sol, D21): every module here reads a sealed canonical model, a key or a verdict sheet, and writes the
paper's evidence artifacts. No runtime module imports this package, so the agent can never see a key or a grade
(``tests/test_pe03c_keys.py`` pins it).
"""

__all__: list[str] = []
