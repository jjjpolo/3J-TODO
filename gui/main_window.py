
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from types import SimpleNamespace

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
        self._subtask_editor = None
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

        # Move Up, Move Down, and Delete Selected buttons in their own frame before tab buttons
        action_btn_frame = tk.Frame(self.root)
        action_btn_frame.pack(side='top', pady=2)
        self.move_up_btn = tk.Button(action_btn_frame, text="Move Up", command=lambda: self._move_selected_task(self.current_tab_id, -1))
        self.move_up_btn.pack(side='left', padx=2)
        self.move_down_btn = tk.Button(action_btn_frame, text="Move Down", command=lambda: self._move_selected_task(self.current_tab_id, 1))
        self.move_down_btn.pack(side='left', padx=2)
        self.del_selected_btn = tk.Button(action_btn_frame, text="Delete Selected", command=lambda: self._delete_selected_task())
        self.del_selected_btn.pack(side='left', padx=2)
        self.expand_btn = tk.Button(action_btn_frame, text="Expand", command=lambda: self._toggle_expand_selected(expand=True))
        self.expand_btn.pack(side='left', padx=2)
        self.collapse_btn = tk.Button(action_btn_frame, text="Collapse", command=lambda: self._toggle_expand_selected(expand=False))
        self.collapse_btn.pack(side='left', padx=2)
        self.expand_btn.config(state='disabled')
        self.collapse_btn.config(state='disabled')
        self.mark_done_btn = tk.Button(action_btn_frame, text="Mark Done", command=self._mark_selected_done)
        self.mark_done_btn.pack(side='left', padx=2)

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
        # Focus entry only if not in history mode
        if not self.show_completed:
            entry.focus_set()
        self._current_entry = entry
        self._current_tree = None

        # Task list as table with expandable/collapsible subtasks
        # Use tree+headings so parent/child rows are actually rendered hierarchically.
        columns = ("completed", "position", "expand")
        self.tree = ttk.Treeview(frame, columns=columns, show="tree headings", selectmode="browse", height=16)
        self.tree.heading("#0", text="Task")
        self.tree.heading("completed", text="Done")
        self.tree.heading("position", text="Pos")
        self.tree.heading("expand", text="")
        self.tree.column("#0", width=220)
        self.tree.column("completed", width=60, anchor="center")
        self.tree.column("position", width=40, anchor="center")
        self.tree.column("expand", width=30, anchor="center")

        # Track expanded/collapsed state
        if not hasattr(self, '_expanded_tasks'):
            self._expanded_tasks = set()

        def insert_task_with_subtasks(todo, parent=""):
            # Top-level tasks are always expanded.
            is_parent_task = parent == ""
            expanded = is_parent_task
            expand_icon = ""
            checkbox = "☑" if todo.completed else "☐"
            sub_count = len(getattr(todo, 'subtasks', [])) if is_parent_task else 0
            base_title = f"{todo.title} ({sub_count})" if is_parent_task and sub_count > 0 else todo.title
            self.tree.insert(parent, "end", iid=str(todo.id), text=base_title, values=(checkbox, todo.position, expand_icon))

            if is_parent_task and expanded:
                for sub in sorted(getattr(todo, 'subtasks', []), key=lambda t: t.position):
                    insert_task_with_subtasks(sub, parent=str(todo.id))
                # Inline subtask input row (empty title) shown only when parent is expanded.
                new_iid = self._new_subtask_iid(todo.id)
                self.tree.insert(
                    str(todo.id),
                    "end",
                    iid=new_iid,
                    text="",
                    values=("", "", "")
                )

        # Get all top-level tasks; fallback to flat tasks when subtask API is not available yet.
        if hasattr(self.controller, 'get_todos_with_subtasks'):
            todos = self.controller.get_todos_with_subtasks(tab_id, completed=self.show_completed)
        else:
            flat_todos = self.controller.get_todos(tab_id, completed=self.show_completed)
            todos = [
                SimpleNamespace(id=t[0], title=t[1], completed=bool(t[2]), position=t[3], subtasks=[])
                for t in flat_todos
            ]
        for todo in sorted(todos, key=lambda t: t.position):
            insert_task_with_subtasks(todo)

        self.tree.pack(side="top", fill="x", padx=5, pady=5)
        self._current_tree = self.tree

        # Bind expand/collapse on expand column click
        def on_tree_click(event):
            # Keep focus behavior for normal clicks.
            self.tree.focus_set()
        self.tree.bind("<Button-1>", on_tree_click)

        # Double-click behavior: expand/collapse parent task or activate inline subtask input.
        def on_double_click(event):
            item = self.tree.identify_row(event.y)
            if not item:
                return

            # Inline subtask entry row.
            if self._is_new_subtask_iid(item):
                parent_id = self._parent_id_from_new_iid(item)
                if parent_id is not None:
                    self._show_subtask_inline_entry(item, parent_id)
                return
        self.tree.bind("<Double-1>", on_double_click)
        # Bind Delete (Supr) key to delete selected task
        self.tree.bind("<Delete>", lambda event: self._delete_selected_task())
        # Focus stays on treeview when clicked or navigated
        self.tree.bind("<Up>", self._on_tree_up_down)
        self.tree.bind("<Down>", self._on_tree_up_down)
        self.tree.bind("<Next>", self._on_tree_page_up_down)
        self.tree.bind("<Prior>", self._on_tree_page_up_down)
        self.tree.bind("<space>", self._on_tree_space)

    def _on_tree_space(self, event):
        self._mark_selected_done()
        return "break"

    def _mark_selected_done(self):
        if not self._current_tree:
            return
        selected = self._current_tree.selection()
        if not selected:
            return
        todo_id = self._todo_id_from_iid(selected[0])
        if todo_id is None:
            return
        values = self._current_tree.item(selected[0], "values")
        if values and values[0] == "☐":
            self.controller.mark_completed(todo_id)
            self._draw_tab_content(self.current_tab_id)

    def _toggle_expand_selected(self, expand=None):
        # Expand/collapse is disabled: tree is always expanded.
        return

    def _on_tree_up_down(self, event):
        tree = self._current_tree
        selected = tree.selection()
        all_items = tree.get_children()
        if not all_items:
            return
        if not selected:
            tree.selection_set(all_items[0])
            tree.focus_set()
            return
        idx = all_items.index(selected[0])
        if event.keysym == "Up" and idx > 0:
            tree.selection_set(all_items[idx-1])
            tree.focus_set()
        elif event.keysym == "Down" and idx < len(all_items)-1:
            tree.selection_set(all_items[idx+1])
            tree.focus_set()
    def _on_tree_page_up_down(self, event):
        tree = self._current_tree
        selected = tree.selection()
        if not selected:
            return
        if event.keysym == "Next":
            self._move_selected_task(self.current_tab_id, 1)
        elif event.keysym == "Prior":
            self._move_selected_task(self.current_tab_id, -1)

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
            todo_id = self._todo_id_from_iid(selected[0])
            if todo_id is None:
                return
            task_title = self.tree.item(selected[0], 'text')
            if messagebox.askyesno("Delete Task", f"Delete task '{task_title}'?"):
                # Find which item should be selected after deletion
                all_items = self.tree.get_children()
                idx = all_items.index(selected[0]) if selected[0] in all_items else 0
                next_focus = None
                if len(all_items) > 1:
                    if idx == 0:
                        next_focus = all_items[1]
                    else:
                        next_focus = all_items[idx-1]
                self.controller.delete_todo(todo_id)
                self._draw_tab_content(self.current_tab_id)
                # After redraw, focus logic:
                if not self.show_completed:
                    tree = self._current_tree
                    if tree and tree.get_children():
                        if next_focus and next_focus in tree.get_children():
                            tree.selection_set(next_focus)
                            tree.focus_set()
                        else:
                            first = tree.get_children()[0]
                            tree.selection_set(first)
                            tree.focus_set()
                    else:
                        if self._current_entry:
                            self._current_entry.focus_set()

    def _move_selected_task(self, tab_id, direction):
        selected = self.tree.selection()
        if not selected:
            return
        selected_iid = selected[0]
        todo_id = self._todo_id_from_iid(selected_iid)
        if todo_id is None:
            return
        moved = False
        if hasattr(self.controller, 'move_todo_hierarchy'):
            moved = self.controller.move_todo_hierarchy(todo_id, direction)

        if not moved:
            return

        # Keep expanded state of current parent where possible and restore selection.
        parent_iid = self.tree.parent(selected_iid)
        if parent_iid and self._todo_id_from_iid(parent_iid) is not None:
            if not hasattr(self, '_expanded_tasks'):
                self._expanded_tasks = set()
            self._expanded_tasks.add(int(parent_iid))

        self._draw_tab_content(tab_id)
        tree = self._current_tree
        moved_id = str(todo_id)
        if tree and tree.exists(moved_id):
            # If moved item became a subtask, auto-expand its new parent and redraw.
            new_parent_iid = tree.parent(moved_id)
            if new_parent_iid and self._todo_id_from_iid(new_parent_iid) is not None:
                if not hasattr(self, '_expanded_tasks'):
                    self._expanded_tasks = set()
                self._expanded_tasks.add(int(new_parent_iid))
                self._draw_tab_content(tab_id)
                tree = self._current_tree
            if tree and tree.exists(moved_id):
                tree.selection_set(moved_id)
                tree.focus_set()

    def _todo_id_from_iid(self, iid):
        try:
            return int(iid)
        except (TypeError, ValueError):
            return None

    def _new_subtask_iid(self, parent_id):
        return f"new_subtask:{parent_id}"

    def _is_new_subtask_iid(self, iid):
        return isinstance(iid, str) and iid.startswith("new_subtask:")

    def _parent_id_from_new_iid(self, iid):
        if not self._is_new_subtask_iid(iid):
            return None
        try:
            return int(iid.split(":", 1)[1])
        except (IndexError, ValueError):
            return None

    def _show_subtask_inline_entry(self, row_iid, parent_id):
        if self._subtask_editor is not None:
            self._subtask_editor.destroy()
            self._subtask_editor = None

        bbox = self.tree.bbox(row_iid, "#0")
        if not bbox:
            return

        x, y, width, height = bbox
        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()
        self._subtask_editor = entry

        def submit_subtask(event=None):
            title = entry.get().strip()
            entry.destroy()
            self._subtask_editor = None
            if not title:
                return
            self.controller.add_todo(title, self.current_tab_id, parent_id=parent_id)
            self._expanded_tasks.add(parent_id)
            self._draw_tab_content(self.current_tab_id)

        def cancel_subtask(event=None):
            if self._subtask_editor is not None:
                self._subtask_editor.destroy()
                self._subtask_editor = None

        entry.bind("<Return>", submit_subtask)
        entry.bind("<Escape>", cancel_subtask)
        entry.bind("<FocusOut>", submit_subtask)

    def _add_task(self, entry, tab_id):
        title = entry.get().strip()
        if title:
            self.controller.add_todo(title, tab_id)
            self._draw_tab_content(tab_id)
            # Refocus entry after adding if not in history mode
            if not self.show_completed and self._current_entry:
                self._current_entry.focus_set()

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
