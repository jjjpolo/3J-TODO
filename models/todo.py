class Todo:
    """Represents a single todo item."""
    def __init__(self, title: str, completed: bool = False):
        self.title = title
        self.completed = completed
