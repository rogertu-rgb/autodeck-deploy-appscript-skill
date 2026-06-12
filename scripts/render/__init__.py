"""
AutoDeck Render Engine — section-by-section HTML generation.

Architecture:
  engine.py     — shared JS generation (utilities, formatting, tables, ECharts)
  shell.py      — HTML shell (CSS, layout, hero, nav, footer)
  section_*.py  — per-section chart functions (one file per section)
  test_harness.py — render single section as standalone HTML for visual testing

Usage:
  from render.engine import Engine
  from render.shell import generate_shell
  from render.test_harness import generate_test_html
"""

__version__ = "0.1.0"
