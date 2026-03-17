
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

class MainWindow:
    def __init__(self, controller):
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("3J TODO App")
        self.tabs = {}
        self.current_tab_id = None
        self.show_completed = False
        self._setup_ui()

    def _setup_ui(self):
        # Tabs
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(fill='both', expand=True)
        self._load_tabs()

        # Add tab button
        add_tab_btn = tk.Button(self.root, text="+ Add Tab", command=self._add_tab_dialog)
        add_tab_btn.pack(side='top', pady=2)

        # History toggle
        self.history_btn = tk.Button(self.root, text="See history", command=self._toggle_history)
        self.history_btn.pack(side='top', pady=2)

    def _load_tabs(self):
        for tab_id, name in self.controller.get_tabs():
            self._add_tab(tab_id, name)
        if not self.tabs:
            self.controller.add_tab("Personal")
            self._add_tab_dialog(refresh=False)

    def _add_tab(self, tab_id, name):
        frame = tk.Frame(self.tab_control)
        self.tab_control.add(frame, text=name)
        self.tabs[tab_id] = frame
        self.tab_control.bind('<<NotebookTabChanged>>', self._on_tab_change)
        if self.current_tab_id is None:
            self.current_tab_id = tab_id
        self._draw_tab_content(tab_id)

    def _add_tab_dialog(self, refresh=True):
        name = simpledialog.askstring("Add Tab", "Tab name:")
        if name:
            self.controller.add_tab(name)
            if refresh:
                self._refresh_tabs()

    def _refresh_tabs(self):
        self.tab_control.forget('all')
        self.tabs.clear()
        self._load_tabs()

    def _on_tab_change(self, event):
        idx = self.tab_control.index(self.tab_control.select())
        tab_ids = list(self.tabs.keys())
        if idx < len(tab_ids):
            self.current_tab_id = tab_ids[idx]
            self._draw_tab_content(self.current_tab_id)

    def _draw_tab_content(self, tab_id):
        frame = self.tabs[tab_id]
        for widget in frame.winfo_children():
            widget.destroy()

        # Add task entry
        entry = tk.Entry(frame)
        entry.pack(side='top', fill='x', padx=5, pady=2)
        add_btn = tk.Button(frame, text="Add Task", command=lambda: self._add_task(entry, tab_id))
        add_btn.pack(side='top', pady=2)

        # Task list
        todos = self.controller.get_todos(tab_id, completed=self.show_completed)
        self.todo_vars = {}
        for todo_id, title, completed, position in todos:
            var = tk.BooleanVar(value=bool(completed))
            cb = tk.Checkbutton(frame, text=title, variable=var, command=lambda tid=todo_id, v=var: self._toggle_complete(tid, v))
            cb.pack(anchor='w')
            self.todo_vars[todo_id] = var
            if not completed:
                del_btn = tk.Button(frame, text="Delete", command=lambda tid=todo_id: self._delete_task(tid))
                del_btn.pack(anchor='e')
        if self.show_completed:
            clear_btn = tk.Button(frame, text="Clear Completed", command=lambda: self._clear_completed(tab_id))
            clear_btn.pack(side='top', pady=2)

        # Reorder (move up/down)
        if not self.show_completed:
            reorder_frame = tk.Frame(frame)
            reorder_frame.pack(side='top', fill='x')
            up_btn = tk.Button(reorder_frame, text="Move Up", command=lambda: self._move_task(tab_id, -1))
            up_btn.pack(side='left')
            down_btn = tk.Button(reorder_frame, text="Move Down", command=lambda: self._move_task(tab_id, 1))
            down_btn.pack(side='left')

    def _add_task(self, entry, tab_id):
        title = entry.get().strip()
        if title:
            self.controller.add_todo(title, tab_id)
            entry.delete(0, 'end')
            self._draw_tab_content(tab_id)

    def _toggle_complete(self, todo_id, var):
        if var.get():
            self.controller.mark_completed(todo_id)
        self._draw_tab_content(self.current_tab_id)

    def _delete_task(self, todo_id):
        self.controller.delete_todo(todo_id)
        self._draw_tab_content(self.current_tab_id)

    def _clear_completed(self, tab_id):
        self.controller.clear_completed(tab_id)
        self._draw_tab_content(tab_id)

    def _toggle_history(self):
        self.show_completed = not self.show_completed
        self.history_btn.config(text="Hide history" if self.show_completed else "See history")
        self._draw_tab_content(self.current_tab_id)

    def _move_task(self, tab_id, direction):
        todos = self.controller.get_todos(tab_id, completed=False)
        if not todos:
            return
        # For simplicity, move the first selected task
        selected = None
        for idx, (todo_id, _, completed, _) in enumerate(todos):
            if self.todo_vars.get(todo_id, tk.BooleanVar()).get() is False:
                selected = idx
                break
        if selected is not None:
            new_idx = selected + direction
            if 0 <= new_idx < len(todos):
                order = [t[0] for t in todos]
                order[selected], order[new_idx] = order[new_idx], order[selected]
                self.controller.reorder_todos(tab_id, order)
                self._draw_tab_content(tab_id)

    def show(self):
        self.root.mainloop()
