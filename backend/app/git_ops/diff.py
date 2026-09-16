from dataclasses import dataclass, field
from enum import Enum

from unidiff import PatchSet


class ChangeType(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    RENAMED = "renamed"


class LineType(str, Enum):
    ADD = "add"
    DEL = "del"
    CONTEXT = "context"


@dataclass
class ChangedLine:
    line_type: LineType
    content: str
    new_line_no: int | None
    old_line_no: int | None


@dataclass
class DiffHunk:
    header: str
    lines: list[ChangedLine] = field(default_factory=list)


@dataclass
class ChangedFile:
    path: str
    old_path: str | None
    change_type: ChangeType
    hunks: list[DiffHunk] = field(default_factory=list)

    def added_line_numbers(self) -> list[int]:
        """New-file line numbers touched by this diff, for anchoring findings."""
        return [
            line.new_line_no
            for hunk in self.hunks
            for line in hunk.lines
            if line.line_type == LineType.ADD and line.new_line_no is not None
        ]


def _strip_prefix(path: str) -> str:
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def _classify_line(line) -> LineType:
    if line.is_added:
        return LineType.ADD
    if line.is_removed:
        return LineType.DEL
    return LineType.CONTEXT


def _classify_file(patched_file) -> ChangeType:
    if patched_file.is_added_file:
        return ChangeType.ADDED
    if patched_file.is_removed_file:
        return ChangeType.DELETED
    if patched_file.is_rename:
        return ChangeType.RENAMED
    return ChangeType.MODIFIED


def parse_diff(diff_text: str) -> list[ChangedFile]:
    """Parse unified diff text (as produced by `git diff`) into our domain model."""
    patch = PatchSet(diff_text)
    changed_files: list[ChangedFile] = []

    for patched_file in patch:
        change_type = _classify_file(patched_file)
        changed_file = ChangedFile(
            path=patched_file.path,
            old_path=_strip_prefix(patched_file.source_file) if change_type == ChangeType.RENAMED else None,
            change_type=change_type,
        )

        for hunk in patched_file:
            diff_hunk = DiffHunk(header=hunk.section_header or "")
            for line in hunk:
                diff_hunk.lines.append(
                    ChangedLine(
                        line_type=_classify_line(line),
                        content=line.value.rstrip("\n"),
                        new_line_no=line.target_line_no,
                        old_line_no=line.source_line_no,
                    )
                )
            changed_file.hunks.append(diff_hunk)

        changed_files.append(changed_file)

    return changed_files
