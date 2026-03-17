from models.todo import Todo

class TodoManager:
    """Handles todo operations and storage."""
    def __init__(self):
        self.todos = []

    def add_todo(self, title: str):
        todo = Todo(title)
        self.todos.append(todo)

    def get_todos(self):
        return self.todos
