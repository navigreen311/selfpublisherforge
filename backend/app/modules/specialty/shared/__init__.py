"""Shared backend services for the Specialty Books module.

Provides cross-cutting concerns used by Children's, Coloring, and Puzzle
book studios:

* **provenance** -- Asset Provenance & Rights Ledger
* **fingerprinting** -- Originality Fingerprinting System
* **spam_detector** -- KDP Spam Risk Detector
* **safety** -- Content Safety (trademark, sensitivity, word-list filters)
* **font_licensing** -- Font License Registry
"""
