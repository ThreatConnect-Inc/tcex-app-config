"""None Model"""

from ..singleton import Singleton


class NoneModel(metaclass=Singleton):
    """A dummy model that return None for all attribute requests."""

    def __getattribute__(self, name: str):
        """Return None for any attribute request."""
        return None
