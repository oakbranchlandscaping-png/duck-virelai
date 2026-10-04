"""RENDER — reads the model, never writes it. LIST 1 / LIST 2 / LIST 3, coverage, diff.

Every stage below emits data (jsonl). This package turns data into what a human reads at the
terminal. One renderer per list; all read the same Model. Six renderers over four holdings
was the defect this package exists to make impossible.
"""
