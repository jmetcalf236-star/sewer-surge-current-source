"""Sewer Surge math calculation layer.

No route/branch choice is accepted here: the book payout is sampled before
serialization and is independent of the player-facing pipe animation.
"""
from src.executables.executables import Executables


class GameCalculations(Executables):
    pass
