"""
Undo/Redo Command Pattern for LexiScholar.
Encapsulates actions like coding, deleting, and renaming to allow reversal.
"""

from abc import ABC, abstractmethod
from typing import List, Any, Optional

class Command(ABC):
    """Base Command interface."""
    @abstractmethod
    def execute(self):
        """Perform the action."""
        pass

    @abstractmethod
    def undo(self):
        """Reverse the action."""
        pass

class CommandStack:
    """Manages undo and redo stacks."""
    def __init__(self, limit=50):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.limit = limit

    def push(self, command: Command):
        """Execute and add command to stack."""
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear() # Clear redo on new action
        
        if len(self.undo_stack) > self.limit:
            self.undo_stack.pop(0)

    def undo(self):
        """Undo last command."""
        if not self.undo_stack:
            return False
        
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        return True

    def redo(self):
        """Redo last undone command."""
        if not self.redo_stack:
            return False
        
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        return True

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0


# --- Concrete Commands ---

class CreateSegmentCommand(Command):
    """Encapsulates creating a coded segment."""
    def __init__(self, segment_dao, doc_id, code_id, start, end, text, weight, coder_id):
        self.dao = segment_dao
        self.data = (doc_id, code_id, start, end, text, weight, coder_id)
        self.segment_id = None

    def execute(self):
        self.segment_id = self.dao.create(*self.data)

    def undo(self):
        if self.segment_id:
            self.dao.delete(self.segment_id)


class DeleteSegmentCommand(Command):
    """Encapsulates deleting a coded segment."""
    def __init__(self, segment_dao, segment_id):
        self.dao = segment_dao
        self.segment_id = segment_id
        self.backup_data = None

    def execute(self):
        # 1. Backup before delete
        self.backup_data = self.dao.get_by_id(self.segment_id)
        # 2. Delete
        self.dao.delete(self.segment_id)

    def undo(self):
        if self.backup_data:
            # Restore using create with original ID to maintain referential integrity
            self.dao.create(
                self.backup_data['document_id'],
                self.backup_data['code_id'],
                self.backup_data['start_pos'],
                self.backup_data['end_pos'],
                self.backup_data['segment_text'],
                self.backup_data['weight'],
                self.backup_data['coder_id'],
                force_id=self.backup_data['id']  # Preserve original ID
            )

class UpdateWeightCommand(Command):
    """Encapsulates updating segment weight."""
    def __init__(self, segment_dao, segment_id, new_weight):
        self.dao = segment_dao
        self.segment_id = segment_id
        self.new_weight = new_weight
        self.old_weight = None

    def execute(self):
        seg = self.dao.get_by_id(self.segment_id)
        if seg:
            self.old_weight = seg['weight']
            self.dao.update_weight(self.segment_id, self.new_weight)

    def undo(self):
        if self.old_weight is not None:
            self.dao.update_weight(self.segment_id, self.old_weight)

class BatchDeleteSegmentsCommand(Command):
    """Encapsulates deleting multiple segments."""
    def __init__(self, segment_dao, segment_ids):
        self.dao = segment_dao
        self.segment_ids = segment_ids
        self.backup_data = []

    def execute(self):
        for sid in self.segment_ids:
            self.backup_data.append(self.dao.get_by_id(sid))
        self.dao.delete_batch(self.segment_ids)

    def undo(self):
        for data in self.backup_data:
            if data:
                self.dao.create(
                    data['document_id'],
                    data['code_id'],
                    data['start_pos'],
                    data['end_pos'],
                    data['segment_text'],
                    data['weight'],
                    data['coder_id'],
                    force_id=data['id']  # Preserve original ID
                )

class InVivoCodingCommand(Command):
    """Encapsulates In-Vivo coding (code creation + segment creation)."""
    def __init__(self, segment_dao, code_dao, doc_id, code_name, color, start, end, text, coder_id):
        self.segment_dao = segment_dao
        self.code_dao = code_dao
        self.doc_id = doc_id
        self.code_name = code_name
        self.color = color
        self.start = start
        self.end = end
        self.text = text
        self.coder_id = coder_id
        
        self.code_id = None
        self.segment_id = None
        self.is_new_code = False

    def execute(self):
        # 1. Find or create code
        existing = next((c for c in self.code_dao.get_all() if c['name'].lower() == self.code_name.lower()), None)
        if existing:
            self.code_id = existing['id']
            self.is_new_code = False
        else:
            self.code_id = self.code_dao.create(self.code_name, self.color, "In-Vivo")
            self.is_new_code = True
            
        # 2. Create segment
        self.segment_id = self.segment_dao.create(self.doc_id, self.code_id, self.start, self.end, self.text, 1, self.coder_id)

    def undo(self):
        if self.segment_id:
            self.segment_dao.delete(self.segment_id)
        if self.is_new_code and self.code_id:
            # We only delete the code if it was created specifically for this command
            # Note: This might be dangerous if other segments were added to it in the meantime, 
            # but for a quick undo it's correct.
            self.code_dao.delete(self.code_id)

# --- Memo Commands ---

class CreateMemoCommand(Command):
    """Encapsulates creating a memo."""
    def __init__(self, memo_dao, content, title=None, doc_id=None, code_id=None, start=None, end=None, coder_id=1):
        self.dao = memo_dao
        self.data = {
            'content': content,
            'title': title,
            'document_id': doc_id,
            'code_id': code_id,
            'start_pos': start,
            'end_pos': end,
            'coder_id': coder_id
        }
        self.memo_id = None

    def execute(self):
        self.memo_id = self.dao.create(**self.data)

    def undo(self):
        if self.memo_id:
            self.dao.delete(self.memo_id)

class UpdateMemoCommand(Command):
    """Encapsulates updating a memo's content."""
    def __init__(self, memo_dao, memo_id, new_content):
        self.dao = memo_dao
        self.memo_id = memo_id
        self.new_content = new_content
        self.old_content = None

    def execute(self):
        memo = self.dao.get_by_id(self.memo_id)
        if memo:
            self.old_content = memo['content']
            self.dao.update(self.memo_id, content=self.new_content)

    def undo(self):
        if self.old_content is not None:
            self.dao.update(self.memo_id, content=self.old_content)

class DeleteMemoCommand(Command):
    """Encapsulates deleting a memo."""
    def __init__(self, memo_dao, memo_id):
        self.dao = memo_dao
        self.memo_id = memo_id
        self.backup_data = None

    def execute(self):
        self.backup_data = self.dao.get_by_id(self.memo_id)
        self.dao.delete(self.memo_id)

    def undo(self):
        if self.backup_data:
            # Restore with original ID to maintain referential integrity
            self.dao.create(
                content=self.backup_data['content'],
                title=self.backup_data['title'],
                document_id=self.backup_data['document_id'],
                code_id=self.backup_data['code_id'],
                start_pos=self.backup_data['start_pos'],
                end_pos=self.backup_data['end_pos'],
                coder_id=self.backup_data['coder_id'],
                force_id=self.backup_data['id']  # Preserve original ID
            )

# --- Code Commands ---

class CreateCodeCommand(Command):
    """Encapsulates creating a new code."""
    def __init__(self, code_dao, name, color, description="", parent_id=None):
        self.dao = code_dao
        self.data = {
            'name': name,
            'color': color,
            'description': description,
            'parent_id': parent_id
        }
        self.code_id = None

    def execute(self):
        self.code_id = self.dao.create(**self.data)

    def undo(self):
        if self.code_id:
            self.dao.delete(self.code_id)

class RenameCodeCommand(Command):
    """Encapsulates renaming a code."""
    def __init__(self, code_dao, code_id, new_name):
        self.dao = code_dao
        self.code_id = code_id
        self.new_name = new_name
        self.old_name = None

    def execute(self):
        code = self.dao.get_by_id(self.code_id)
        if code:
            self.old_name = code['name']
            self.dao.update(self.code_id, name=self.new_name)

    def undo(self):
        if self.old_name:
            self.dao.update(self.code_id, name=self.old_name)

class DeleteCodeCommand(Command):
    """Encapsulates deleting a code (and its segments!). Warning: Heavy operation."""
    def __init__(self, code_dao, segment_dao, code_id):
        self.code_dao = code_dao
        self.segment_dao = segment_dao
        self.code_id = code_id
        self.backup_code = None
        self.backup_segments = []

    def execute(self):
        # 1. Backup Code
        self.backup_code = self.code_dao.get_by_id(self.code_id)
        # 2. Backup Segments
        self.backup_segments = self.segment_dao.get_by_code(self.code_id)
        
        # 3. Delete (Code DAO cascade deletes segments usually, or we do it manually?)
        # Ideally DB handles cascade, but let's assume DAO logic handles it or we do nothing if cascade
        # Let's rely on DAO delete which should handle it.
        self.code_dao.delete(self.code_id)

    def undo(self):
        if self.backup_code:
            # Restore Code with original ID
            restored_code_id = self.code_dao.create(
                self.backup_code['name'],
                self.backup_code['color'],
                self.backup_code['description'],
                self.backup_code['parent_id'],
                force_id=self.backup_code['id']  # Preserve original ID
            )
            
            # Restore Segments (mapped to restored code ID)
            for seg in self.backup_segments:
                self.segment_dao.create(
                    seg['document_id'],
                    restored_code_id,
                    seg['start_pos'],
                    seg['end_pos'],
                    seg['segment_text'],
                    seg['weight'],
                    seg['coder_id'],
                    force_id=seg['id']  # Preserve original segment ID
                )


# --- Paraphrase Command ---

class UpdateParaphraseCommand(Command):
    """Encapsulates updating or clearing a segment's paraphrase.
    Fully undo/redo-able via the global CommandStack.
    """
    def __init__(self, segment_dao, segment_id: int, new_text: str, old_text: str = ""):
        self.dao = segment_dao
        self.segment_id = segment_id
        self.new_text = new_text
        self.old_text = old_text

    def execute(self):
        self.dao.update_paraphrase(self.segment_id, self.new_text)

    def undo(self):
        self.dao.update_paraphrase(self.segment_id, self.old_text)

class UpdateCommentCommand(Command):
    """Encapsulates updating or clearing a segment's comment/note.
    Fully undo/redo-able via the global CommandStack.
    """
    def __init__(self, segment_dao, segment_id: int, new_text: str, old_text: str = ""):
        self.dao = segment_dao
        self.segment_id = segment_id
        self.new_text = new_text
        self.old_text = old_text

    def execute(self):
        self.dao.update_comment(self.segment_id, self.new_text)

    def undo(self):
        self.dao.update_comment(self.segment_id, self.old_text)
