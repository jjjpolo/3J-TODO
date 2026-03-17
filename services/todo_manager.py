
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
                    position INTEGER,
                    FOREIGN KEY(tab_id) REFERENCES tabs(id)
                )
            ''')
        logger.debug('Tables ensured in SQLite DB.')

    def add_tab(self, name: str):
        with self.conn:
            self.conn.execute('INSERT OR IGNORE INTO tabs (name) VALUES (?)', (name,))
        logger.info(f'Tab added: {name}')

    def get_tabs(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id, name FROM tabs')
        return cur.fetchall()

    def add_todo(self, title: str, tab_id: int):
        with self.conn:
            cur = self.conn.execute('SELECT COALESCE(MAX(position), 0) + 1 FROM todos WHERE tab_id=? AND completed=0', (tab_id,))
            position = cur.fetchone()[0]
            self.conn.execute('INSERT INTO todos (title, completed, tab_id, position) VALUES (?, 0, ?, ?)', (title, tab_id, position))
        logger.info(f'Todo added: {title} (tab_id={tab_id})')

    def get_todos(self, tab_id: int, completed: bool = False):
        cur = self.conn.cursor()
        cur.execute('SELECT id, title, completed, position FROM todos WHERE tab_id=? AND completed=? ORDER BY position', (tab_id, int(completed)))
        return cur.fetchall()

    def mark_completed(self, todo_id: int):
        with self.conn:
            self.conn.execute('UPDATE todos SET completed=1 WHERE id=?', (todo_id,))
        logger.info(f'Todo marked completed: {todo_id}')

    def delete_todo(self, todo_id: int):
        with self.conn:
            self.conn.execute('DELETE FROM todos WHERE id=?', (todo_id,))
        logger.info(f'Todo deleted: {todo_id}')

    def reorder_todos(self, tab_id: int, new_order: list):
        with self.conn:
            for position, todo_id in enumerate(new_order, 1):
                self.conn.execute('UPDATE todos SET position=? WHERE id=? AND tab_id=?', (position, todo_id, tab_id))
        logger.info(f'Todos reordered in tab {tab_id}: {new_order}')

    def clear_completed(self, tab_id: int):
        with self.conn:
            self.conn.execute('DELETE FROM todos WHERE tab_id=? AND completed=1', (tab_id,))
        logger.info(f'Completed todos cleared from tab {tab_id}')
