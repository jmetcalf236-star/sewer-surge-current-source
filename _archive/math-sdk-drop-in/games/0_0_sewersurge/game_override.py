"""Game-specific extension point for the official Stake Engine Math SDK."""
from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    def reset_book(self) -> None:
        super().reset_book()

    def check_game_repeat(self) -> None:
        # Criteria validation is implemented by GameState.check_repeat().
        return None
