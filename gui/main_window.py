
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
        # Pre-create clear_completed_btn to avoid AttributeError
        self.clear_completed_btn = None
        self._setup_ui()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_ui(self):
        # Tabs
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(fill='both', expand=True)
        self._load_tabs()

        # Add/Delete tab buttons in a frame
        tab_btn_frame = tk.Frame(self.root)
        tab_btn_frame.pack(side='top', pady=2)
        add_tab_btn = tk.Button(tab_btn_frame, text="+ Add Tab", command=self._add_tab_dialog)
        add_tab_btn.pack(side='left', padx=2)
        del_tab_btn = tk.Button(tab_btn_frame, text="Delete Tab", command=self._delete_current_tab)
        del_tab_btn.pack(side='left', padx=2)

        # History toggle and Clear Completed in a frame
        top_action_frame = tk.Frame(self.root)
        top_action_frame.pack(side='top', pady=2)
        self.history_btn = tk.Button(top_action_frame, text="See history", command=self._toggle_history)
        self.history_btn.pack(side='left', padx=2)
        self.clear_completed_btn = tk.Button(top_action_frame, text="Clear Completed", command=self._clear_completed_top)
        self.clear_completed_btn.pack(side='left', padx=2)
        self.clear_completed_btn.pack_forget()  # Hide by default
    def _delete_current_tab(self):
        if len(self.tabs) <= 1:
            messagebox.showinfo("Delete Tab", "At least one tab must remain.")
            return
        idx = self.tab_control.index(self.tab_control.select())
        tab_ids = list(self.tabs.keys())
        if idx < len(tab_ids):
            tab_id = tab_ids[idx]
            tab_name = self.tab_control.tab(idx, "text")
            if messagebox.askyesno("Delete Tab", f"Delete tab '{tab_name}' and all its tasks?"):
                self.controller.delete_tab(tab_id)
                self._refresh_tabs()

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
        # Remove all tabs from the notebook
        for tab_id in self.tab_control.tabs():
            self.tab_control.forget(tab_id)
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

        # Add task entry and button on same line
        entry_frame = tk.Frame(frame)
        entry_frame.pack(side='top', fill='x', padx=5, pady=2)
        entry = tk.Entry(entry_frame)
        entry.pack(side='left', fill='x', expand=True)
        add_btn = tk.Button(entry_frame, text="Add Task", command=lambda: self._add_task(entry, tab_id))
        add_btn.pack(side='left', padx=5)
        # Bind Enter key to add task
        entry.bind('<Return>', lambda event: self._add_task(entry, tab_id))
        # Always focus the entry field after drawing
        entry.focus_set()

        # Task list as table
        todos = self.controller.get_todos(tab_id, completed=self.show_completed)
        columns = ("completed", "title", "position")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse", height=10)
        self.tree.heading("completed", text="Done")
        if self.show_completed:
            self.tree.heading("title", text="Completed task")
        else:
            self.tree.heading("title", text="Task")
        self.tree.heading("position", text="Pos")
        self.tree.column("completed", width=60, anchor="center")
        self.tree.column("title", width=250)
        self.tree.column("position", width=40, anchor="center")

        # Insert tasks
        for todo_id, title, completed, position in todos:
            checkbox = "☑" if completed else "☐"
            self.tree.insert("", "end", iid=str(todo_id), values=(checkbox, title, position))


        self.tree.pack(side="top", fill="x", padx=5, pady=5)

        # Double-click to toggle completion
        def on_double_click(event):
            item = self.tree.identify_row(event.y)
            if item:
                todo_id = int(item)
                # Only allow marking as completed if not already
                values = self.tree.item(item, "values")
                if values[0] == "☐":
                    self.controller.mark_completed(todo_id)
                    self._draw_tab_content(tab_id)
        self.tree.bind("<Double-1>", on_double_click)
        # Bind Delete (Supr) key to delete selected task
        self.tree.bind("<Delete>", lambda event: self._delete_selected_task())

        # Delete and Move Up/Down buttons on same line
        btn_frame = tk.Frame(frame)
        btn_frame.pack(side='top', fill='x', pady=2)
        tk.Label(btn_frame).pack(side='left', expand=True)  # left spacer
        up_btn = tk.Button(btn_frame, text="Move Up", command=lambda: self._move_selected_task(tab_id, -1))
        up_btn.pack(side='left', padx=2)
        down_btn = tk.Button(btn_frame, text="Move Down", command=lambda: self._move_selected_task(tab_id, 1))
        down_btn.pack(side='left', padx=2)
        del_btn = tk.Button(btn_frame, text="Delete Selected", command=lambda: self._delete_selected_task())
        del_btn.pack(side='left', padx=2)
        tk.Label(btn_frame).pack(side='left', expand=True)  # right spacer

        # Show or hide the top clear completed button
        if self.clear_completed_btn:
            if self.show_completed:
                self.clear_completed_btn.pack(side='left', padx=2)
            else:
                self.clear_completed_btn.pack_forget()

    def _clear_completed_top(self):
        if self.current_tab_id is not None:
            self._clear_completed(self.current_tab_id)

    def _delete_selected_task(self):
        selected = self.tree.selection()
        if selected:
            todo_id = int(selected[0])
            task_title = self.tree.item(selected[0], 'values')[1]
            if messagebox.askyesno("Delete Task", f"Delete task '{task_title}'?"):
                self.controller.delete_todo(todo_id)
                self._draw_tab_content(self.current_tab_id)

    def _move_selected_task(self, tab_id, direction):
        selected = self.tree.selection()
        if not selected:
            return
        todo_id = int(selected[0])
        todos = self.controller.get_todos(tab_id, completed=False)
        order = [t[0] for t in todos]
        if todo_id not in order:
            return
        idx = order.index(todo_id)
        new_idx = idx + direction
        if 0 <= new_idx < len(order):
            order[idx], order[new_idx] = order[new_idx], order[idx]
            self.controller.reorder_todos(tab_id, order)
            # Redraw and reselect the moved item
            self._draw_tab_content(tab_id)
            # Reselect the moved item
            self.tree.selection_set(str(order[new_idx]))

    def _add_task(self, entry, tab_id):
        title = entry.get().strip()
        if title:
            self.controller.add_todo(title, tab_id)
            # Do not call entry.focus_set() here, as the widget will be destroyed
            # entry.delete(0, 'end') is also unnecessary since the redraw will create a new entry
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
