class Todo:
    """Represents a single todo item, which may have subtasks."""
    def __init__(self, title: str, completed: bool = False, position: int = 0, parent_id: int = None, todo_id: int = None, completed_at: str = None):
        self.id = todo_id
        self.title = title
        self.completed = completed
        self.position = position
        self.parent_id = parent_id  # None if this is a top-level task
        self.completed_at = completed_at
        self.subtasks = []  # List of Todo instances

    def add_subtask(self, subtask):
        self.subtasks.append(subtask)
        self.subtasks.sort(key=lambda t: t.position)

    def remove_subtask(self, subtask_id):
        self.subtasks = [s for s in self.subtasks if s.id != subtask_id]

    def get_subtask(self, subtask_id):
        for s in self.subtasks:
            if s.id == subtask_id:
                return s
        return None
