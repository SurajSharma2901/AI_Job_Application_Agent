"""
Base interface and universal methods for all ATS platforms.
"""
from src.state import ApplicationState

class BaseATSAdapter:
    async def apply(self, page, state: ApplicationState) -> ApplicationState:
        raise NotImplementedError("This method must be overridden by specific ATS adapters.")
