from services.todo_manager import TodoManager
from gui.main_window import MainWindow

class AppController:
    def __init__(self):
        self.todo_manager = TodoManager()
        self.main_window = MainWindow(self)

    def run(self):
        self.main_window.show()
