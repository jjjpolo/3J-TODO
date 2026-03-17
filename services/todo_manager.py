
import sqlite3
import os
from models.todo import Todo
from services.logger import logger

DB_FILE = os.path.join(os.path.dirname(__file__), '../todo.db')

class TodoManager:
    """Handles todo operations and storage using SQLite."""

    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self._create_tables()
        logger.info('TodoManager initialized with SQLite DB.')

    def delete_tab(self, tab_id: int):
        with self.conn:
            self.conn.execute('DELETE FROM todos WHERE tab_id=?', (tab_id,))
            self.conn.execute('DELETE FROM tabs WHERE id=?', (tab_id,))
        logger.info(f'Tab deleted: {tab_id}')

    def _create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS tabs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    tab_id INTEGER,
                    parent_id INTEGER,
                    position INTEGER,
                    FOREIGN KEY(tab_id) REFERENCES tabs(id),
                    FOREIGN KEY(parent_id) REFERENCES todos(id)
                )
            ''')
            # Backward-compatible migration for existing DBs without parent_id.
            cur = self.conn.execute("PRAGMA table_info(todos)")
            columns = [row[1] for row in cur.fetchall()]
            if 'parent_id' not in columns:
                self.conn.execute('ALTER TABLE todos ADD COLUMN parent_id INTEGER')
        logger.debug('Tables ensured in SQLite DB.')

    def add_tab(self, name: str):
        with self.conn:
            self.conn.execute('INSERT OR IGNORE INTO tabs (name) VALUES (?)', (name,))
        logger.info(f'Tab added: {name}')

    def get_tabs(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id, name FROM tabs')
        return cur.fetchall()

    def add_todo(self, title: str, tab_id: int, parent_id: int = None):
        with self.conn:
            if parent_id is None:
                cur = self.conn.execute(
                    'SELECT COALESCE(MAX(position), 0) + 1 FROM todos WHERE tab_id=? AND completed=0 AND parent_id IS NULL',
                    (tab_id,)
                )
            else:
                cur = self.conn.execute(
                    'SELECT COALESCE(MAX(position), 0) + 1 FROM todos WHERE tab_id=? AND completed=0 AND parent_id=?',
                    (tab_id, parent_id)
                )
            position = cur.fetchone()[0]
            self.conn.execute(
                'INSERT INTO todos (title, completed, tab_id, parent_id, position) VALUES (?, 0, ?, ?, ?)',
                (title, tab_id, parent_id, position)
            )
        logger.info(f'Todo added: {title} (tab_id={tab_id}, parent_id={parent_id})')

    def get_todos(self, tab_id: int, completed: bool = False):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT id, title, completed, position FROM todos WHERE tab_id=? AND completed=? AND parent_id IS NULL ORDER BY position',
            (tab_id, int(completed))
        )
        return cur.fetchall()

    def get_todos_with_subtasks(self, tab_id: int, completed: bool = False):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT id, title, completed, position FROM todos WHERE tab_id=? AND completed=? AND parent_id IS NULL ORDER BY position',
            (tab_id, int(completed))
        )
        parent_rows = cur.fetchall()

        cur.execute(
            'SELECT id, title, completed, position, parent_id FROM todos WHERE tab_id=? AND completed=? AND parent_id IS NOT NULL ORDER BY parent_id, position',
            (tab_id, int(completed))
        )
        sub_rows = cur.fetchall()

        parent_map = {}
        parents = []
        for row in parent_rows:
            todo = Todo(row[1], bool(row[2]), row[3], None, row[0])
            parent_map[row[0]] = todo
            parents.append(todo)

        for row in sub_rows:
            sub = Todo(row[1], bool(row[2]), row[3], row[4], row[0])
            parent = parent_map.get(row[4])
            if parent:
                parent.add_subtask(sub)

        return parents

    def mark_completed(self, todo_id: int):
        with self.conn:
            row = self._get_todo_row_with_title(todo_id)
            if not row:
                return

            # Subtask completion: move to completed parent grouped by parent title.
            if row['parent_id'] is not None and row['completed'] == 0:
                parent = self._get_todo_row_with_title(row['parent_id'])
                if not parent:
                    # Fallback: mark completed in place if parent is missing.
                    self.conn.execute('UPDATE todos SET completed=1 WHERE id=?', (todo_id,))
                    logger.info(f'Subtask marked completed without parent fallback: {todo_id}')
                    return

                completed_parent_id = self._find_or_create_completed_parent_by_title(
                    tab_id=row['tab_id'],
                    parent_title=parent['title']
                )

                cur = self.conn.execute(
                    'SELECT COALESCE(MAX(position), 0) + 1 FROM todos WHERE parent_id=? AND completed=1',
                    (completed_parent_id,)
                )
                new_pos = cur.fetchone()[0]

                self.conn.execute(
                    'UPDATE todos SET completed=1, parent_id=?, position=? WHERE id=?',
                    (completed_parent_id, new_pos, todo_id)
                )
                logger.info(
                    f'Subtask marked completed and moved under completed parent: subtask={todo_id}, completed_parent={completed_parent_id}'
                )
                return

            # Default behavior for top-level tasks and already-completed items.
            self.conn.execute('UPDATE todos SET completed=1 WHERE id=?', (todo_id,))
        logger.info(f'Todo marked completed: {todo_id}')

    def _get_todo_row_with_title(self, todo_id: int):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT id, tab_id, parent_id, position, completed, title FROM todos WHERE id=?',
            (todo_id,)
        )
        r = cur.fetchone()
        if not r:
            return None
        return {
            'id': r[0],
            'tab_id': r[1],
            'parent_id': r[2],
            'position': r[3],
            'completed': r[4],
            'title': r[5],
        }

    def _find_or_create_completed_parent_by_title(self, tab_id: int, parent_title: str):
        cur = self.conn.cursor()
        cur.execute(
            '''
            SELECT id FROM todos
            WHERE tab_id=? AND completed=1 AND parent_id IS NULL AND title=?
            ORDER BY id ASC LIMIT 1
            ''',
            (tab_id, parent_title)
        )
        found = cur.fetchone()
        if found:
            return found[0]

        cur.execute(
            'SELECT COALESCE(MAX(position), 0) + 1 FROM todos WHERE tab_id=? AND completed=1 AND parent_id IS NULL',
            (tab_id,)
        )
        new_pos = cur.fetchone()[0]
        cur.execute(
            'INSERT INTO todos (title, completed, tab_id, parent_id, position) VALUES (?, 1, ?, NULL, ?)',
            (parent_title, tab_id, new_pos)
        )
        return cur.lastrowid

    def delete_todo(self, todo_id: int):
        with self.conn:
            self.conn.execute('DELETE FROM todos WHERE parent_id=?', (todo_id,))
            self.conn.execute('DELETE FROM todos WHERE id=?', (todo_id,))
        logger.info(f'Todo deleted: {todo_id}')

    def reorder_todos(self, tab_id: int, new_order: list):
        with self.conn:
            for position, todo_id in enumerate(new_order, 1):
                self.conn.execute(
                    'UPDATE todos SET position=? WHERE id=? AND tab_id=? AND parent_id IS NULL',
                    (position, todo_id, tab_id)
                )
        logger.info(f'Todos reordered in tab {tab_id}: {new_order}')

    def reorder_subtasks(self, parent_id: int, new_order: list):
        with self.conn:
            for position, todo_id in enumerate(new_order, 1):
                self.conn.execute(
                    'UPDATE todos SET position=? WHERE id=? AND parent_id=?',
                    (position, todo_id, parent_id)
                )
        logger.info(f'Subtasks reordered for parent {parent_id}: {new_order}')

    def clear_completed(self, tab_id: int):
        with self.conn:
            self.conn.execute('DELETE FROM todos WHERE tab_id=? AND completed=1', (tab_id,))
        logger.info(f'Completed todos cleared from tab {tab_id}')

    def move_todo_hierarchy(self, todo_id: int, direction: int):
        """
        Hierarchy-aware move:
        - Up on top-level task: becomes subtask of the top-level task above.
        - Up on subtask: promoted to top-level at parent's position.
        - Down on subtask: promoted to top-level after parent.
        - Down on top-level task: regular top-level reorder down.
        """
        with self.conn:
            row = self._get_todo_row(todo_id)
            if not row:
                return False

            if row['parent_id'] is None:
                if direction < 0:
                    moved = self._demote_task_to_previous_parent(row)
                else:
                    moved = self._move_top_level_down(row)
            else:
                if direction < 0:
                    moved = self._promote_subtask(row, before_parent=True)
                else:
                    moved = self._promote_subtask(row, before_parent=False)

            if moved:
                self._normalize_positions(row['tab_id'], row['completed'])
            return moved

    def _get_todo_row(self, todo_id: int):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT id, tab_id, parent_id, position, completed FROM todos WHERE id=?',
            (todo_id,)
        )
        r = cur.fetchone()
        if not r:
            return None
        return {
            'id': r[0],
            'tab_id': r[1],
            'parent_id': r[2],
            'position': r[3],
            'completed': r[4],
        }

    def _demote_task_to_previous_parent(self, row):
        cur = self.conn.cursor()
        cur.execute(
            '''
            SELECT id FROM todos
            WHERE tab_id=? AND completed=? AND parent_id IS NULL AND position < ?
            ORDER BY position DESC LIMIT 1
            ''',
            (row['tab_id'], row['completed'], row['position'])
        )
        prev = cur.fetchone()
        if not prev:
            return False
        new_parent_id = prev[0]

        cur.execute(
            'SELECT COALESCE(MAX(position), 0) + 1 FROM todos WHERE parent_id=? AND completed=?',
            (new_parent_id, row['completed'])
        )
        new_pos = cur.fetchone()[0]

        self.conn.execute(
            'UPDATE todos SET parent_id=?, position=? WHERE id=?',
            (new_parent_id, new_pos, row['id'])
        )
        return True

    def _promote_subtask(self, row, before_parent: bool):
        parent = self._get_todo_row(row['parent_id'])
        if not parent:
            return False

        insert_pos = parent['position'] if before_parent else parent['position'] + 1

        # Make room in top-level list.
        self.conn.execute(
            '''
            UPDATE todos
            SET position = position + 1
            WHERE tab_id=? AND completed=? AND parent_id IS NULL AND position >= ?
            ''',
            (row['tab_id'], row['completed'], insert_pos)
        )

        self.conn.execute(
            'UPDATE todos SET parent_id=NULL, position=? WHERE id=?',
            (insert_pos, row['id'])
        )
        return True

    def _move_top_level_down(self, row):
        cur = self.conn.cursor()
        cur.execute(
            '''
            SELECT id, position FROM todos
            WHERE tab_id=? AND completed=? AND parent_id IS NULL AND position > ?
            ORDER BY position ASC LIMIT 1
            ''',
            (row['tab_id'], row['completed'], row['position'])
        )
        nxt = cur.fetchone()
        if not nxt:
            return False
        next_id, next_pos = nxt
        self.conn.execute('UPDATE todos SET position=? WHERE id=?', (next_pos, row['id']))
        self.conn.execute('UPDATE todos SET position=? WHERE id=?', (row['position'], next_id))
        return True

    def _normalize_positions(self, tab_id: int, completed: int):
        # Normalize top-level order.
        cur = self.conn.cursor()
        cur.execute(
            '''
            SELECT id FROM todos
            WHERE tab_id=? AND completed=? AND parent_id IS NULL
            ORDER BY position, id
            ''',
            (tab_id, completed)
        )
        for idx, (tid,) in enumerate(cur.fetchall(), 1):
            self.conn.execute('UPDATE todos SET position=? WHERE id=?', (idx, tid))

        # Normalize each parent's subtasks.
        cur.execute(
            '''
            SELECT id FROM todos
            WHERE tab_id=? AND completed=? AND parent_id IS NULL
            ''',
            (tab_id, completed)
        )
        parent_ids = [r[0] for r in cur.fetchall()]
        for pid in parent_ids:
            cur.execute(
                'SELECT id FROM todos WHERE parent_id=? AND completed=? ORDER BY position, id',
                (pid, completed)
            )
            for idx, (sid,) in enumerate(cur.fetchall(), 1):
                self.conn.execute('UPDATE todos SET position=? WHERE id=?', (idx, sid))
