# The Instrument Ruling — project charter

Director ruling, 2026-08-22, verbatim:

> **The hybrid is a lab instrument. Score on the ARC-AGI-3 Kaggle leaderboard is its goal
> and the Kaggle hidden set is its external oracle. It may run existing Virelai code as-is
> and may adopt instrument conventions without ruling them. Nothing in this project is ever
> citable as precedent in the golden build. O-8 and O-9 remain open.**

Consequences, binding on all work in this repository:

1. This project is a competition entry, not the Virelai solver. Its oracle is the Kaggle
   hidden set; its goal is score.
2. Instrument conventions (e.g. the threader's correspondence rule) are adopted, not ruled.
   They carry no precedential weight anywhere else.
3. The golden build's tree is never read, written, or imported by this project except where
   a work order explicitly names a legacy unit to run or measure — and then read-only.
4. The repository boundary is the disclosure boundary: what is open-sourced at milestone is
   exactly and only what is in this repository.
