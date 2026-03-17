from services.todo_manager import TodoManager
from gui.main_window import MainWindow

class AppController:
    def __init__(self):
        self.todo_manager = TodoManager()
        self.main_window = MainWindow(self)
        # Placeholder for user login support in the future
        self.current_user = None

    def run(self):
        self.main_window.show()

    # Tab management
    def get_tabs(self):
        return self.todo_manager.get_tabs()

    def add_tab(self, name):
        self.todo_manager.add_tab(name)

    def delete_tab(self, tab_id):
        self.todo_manager.delete_tab(tab_id)

    # Todo management
    def add_todo(self, title, tab_id, parent_id=None):
        self.todo_manager.add_todo(title, tab_id, parent_id)

    def get_todos(self, tab_id, completed=False):
        return self.todo_manager.get_todos(tab_id, completed)

    def get_todos_with_subtasks(self, tab_id, completed=False):
        return self.todo_manager.get_todos_with_subtasks(tab_id, completed)

    def mark_completed(self, todo_id):
        self.todo_manager.mark_completed(todo_id)

    def delete_todo(self, todo_id):
        self.todo_manager.delete_todo(todo_id)

    def reorder_todos(self, tab_id, new_order):
        self.todo_manager.reorder_todos(tab_id, new_order)

    def reorder_subtasks(self, parent_id, new_order):
        self.todo_manager.reorder_subtasks(parent_id, new_order)

    def move_todo_hierarchy(self, todo_id, direction):
        return self.todo_manager.move_todo_hierarchy(todo_id, direction)

    def clear_completed(self, tab_id):
        self.todo_manager.clear_completed(tab_id)

    def shift_completed_date(self, todo_id, day_delta):
        return self.todo_manager.shift_completed_date(todo_id, day_delta)
