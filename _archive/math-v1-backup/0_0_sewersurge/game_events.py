"""Standard SDK events are emitted from src.events.events.

Sewer Surge adds three versioned book events in GameState:
- sewerBoard: authoritative 5x5 row-major board, rotations and inlet
- sewerFeature: scatter feature tier (bonus or deep-run)
- sewerAward: authoritative award in integer cents (SDK book units)
"""
from src.events.events import *  # noqa: F401,F403
