from collections import deque


class Command:
    """Base class for an undoable operation."""

    def execute(self):
        """Perform the action."""

    def undo(self):
        """Reverse the action."""

    def redo(self):
        """Re-perform the action (defaults to execute)."""
        self.execute()

    def merge(self, other):
        """Try to merge with the previous command of the same type.
        Return True if merged (no new entry needed)."""
        return False


class UndoRedoManager:
    """Stores a stack of commands and supports undo/redo."""

    def __init__(self, max_size=100):
        self._undo_stack = deque(maxlen=max_size)
        self._redo_stack = deque(maxlen=max_size)
        self._saved_index = 0  # position of last save (for dirty tracking)

    @property
    def can_undo(self):
        return len(self._undo_stack) > 0

    @property
    def can_redo(self):
        return len(self._redo_stack) > 0

    def push(self, command):
        self._redo_stack.clear()
        if self._undo_stack and command.merge(self._undo_stack[-1]):
            return
        command.execute()
        self._undo_stack.append(command)

    def undo(self):
        if not self._undo_stack:
            return
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)

    def redo(self):
        if not self._redo_stack:
            return
        cmd = self._redo_stack.pop()
        cmd.redo()
        self._undo_stack.append(cmd)

    def mark_saved(self):
        self._saved_index = len(self._undo_stack)

    @property
    def is_dirty(self):
        return len(self._undo_stack) != self._saved_index

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._saved_index = 0
