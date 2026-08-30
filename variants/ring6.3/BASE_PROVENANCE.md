# Ring 6.3 base provenance

Ring 6.3 was seeded from the exact assembled ARC source used by the completed
Ring 6.2 Kaggle run:

`kaggle/ring6.2/source-dataset/src/ARC3-Inference/`

Destination:

`variants/ring6.3/ARC3-Inference/`

The partial `variants/ring6.2/ARC3-Inference/` overlay was not used as the ARC
base. It has only five inference files and cannot run independently; the
executed assembled tree has 31.

Excluded during the seed copy:

- `__pycache__/`;
- `*.pyc`;
- space-suffixed duplicate directories matching `* 2/` or `* 3/`.

The excluded duplicates were empty. They remain untouched in historical Ring
6.2 material. Ring 6.3 hygiene rejects their reappearance in source or bundle.

Only the Ring 6.3 transport files and release documentation may differ from
the clean executed base. Verification compares all other files by SHA-256
before Kaggle assembly.
