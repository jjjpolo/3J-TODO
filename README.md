# 3J TODO App

A lightweight desktop TODO application built with Python and Tkinter, backed by a local SQLite database.

## Features

- **Tabs** — organise tasks across multiple named lists (e.g. Personal, Work).
- **Tasks & Subtasks** — tasks can have subtasks; expand or collapse them using the native disclosure triangle.
- **Keyboard-first navigation** — move focus and reorder items without leaving the keyboard.
- **History view** — completed tasks are kept and grouped by the day they were finished; completion dates can be adjusted after the fact.
- **Persistent storage** — everything is saved automatically to `todo.db` (SQLite); no manual save required.

## Requirements

- Python 3.9+
- No external dependencies — only the Python standard library (`tkinter`, `sqlite3`).

## Running the app

```bash
python main.py
```

## Quick how-to

### Managing tabs
| Action | How |
|---|---|
| Add a new tab | Click **+ Add Tab** and enter a name |
| Delete the current tab | Click **Delete Tab** (requires at least one tab to remain) |

### Managing tasks
| Action | How |
|---|---|
| Add a task | Type in the text field at the top of the tab and press **Enter** or click **Add Task** |
| Add a subtask | Double-click the blank row inside an expanded parent task and type the subtask title, then press **Enter** |
| Mark a task/subtask done | Select it and press **Space** or click **Mark Done** |
| Delete a task | Select it and press **Delete** or click **Delete Selected** (confirmation required) |

### Keyboard navigation & reordering
| Key | Action (normal view) |
|---|---|
| ↑ / ↓ | Move selection up / down |
| Page Up | Move selected item up in the list (hierarchy-aware) |
| Page Down | Move selected item down in the list (hierarchy-aware) |
| Space | Mark selected item as done |
| Delete | Delete selected item |

Hierarchy-aware movement means:
- Moving a **top-level task** up/down converts it into a subtask of the neighbouring task.
- Moving the **first subtask** up promotes it to a top-level task above its parent.
- Moving the **last subtask** down promotes it to a top-level task below its parent.

### History view
Click **See history** to switch to the history view, where completed items are shown grouped by the date they were completed.

| Key / Button | Action (history view) |
|---|---|
| ↑ / ↓ | Move selection up / down (navigation only) |
| Page Up | Increase the completion date of the selected item by **+1 day** |
| Page Down | Decrease the completion date of the selected item by **−1 day** |
| **Increase Date** button | Same as Page Up |
| **Decrease Date** button | Same as Page Down |
| **Clear Completed** button | Permanently delete all completed items in the current tab |

A task can appear in **multiple date groups** if its subtasks were completed on different days.

## Project structure

```
3J-TODO/
├── main.py                  # Entry point
├── config.json              # App configuration (log level, etc.)
├── todo.db                  # SQLite database (auto-created, git-ignored)
├── models/
│   └── todo.py              # Todo data class
├── services/
│   ├── todo_manager.py      # All database logic and business rules
│   └── logger.py            # Logging setup
├── controllers/
│   └── app_controller.py    # Bridge between GUI and service layer
└── gui/
    └── main_window.py       # Tkinter UI (VERSION constant lives here)
```

## Versioning

The current version is defined as `VERSION` in `gui/main_window.py` and is shown in the title bar.
