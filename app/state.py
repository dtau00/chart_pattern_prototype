"""Application-wide state management."""


class AppState:
    """Application-wide state management.

    Separates JSON-serializable data from complex Python objects
    to avoid serialization errors in NiceGUI.
    """
    def __init__(self):
        # Simple, JSON-serializable data (strings, numbers, lists, dicts)
        self.data = {}
        # Complex Python objects (DataFrames, custom classes, etc.)
        self._objects = {}

    def get(self, key, default=None):
        """Get value from either data or objects storage."""
        if key in self.data:
            return self.data[key]
        return self._objects.get(key, default)

    def set(self, key, value):
        """Set value in appropriate storage based on type."""
        # Check if value is JSON-serializable
        if self._is_json_serializable(value):
            self.data[key] = value
        else:
            self._objects[key] = value
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getitem__(self, key):
        """Get value, checking both storages."""
        if key in self.data:
            return self.data[key]
        if key in self._objects:
            return self._objects[key]
        raise KeyError(key)

    def __contains__(self, key):
        return key in self.data or key in self._objects

    @staticmethod
    def _is_json_serializable(value):
        """Check if a value is JSON serializable."""
        import json
        try:
            json.dumps(value)
            return True
        except (TypeError, ValueError):
            return False


# Initialize global app state
app_state = AppState()
