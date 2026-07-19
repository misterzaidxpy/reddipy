"""CSV exporter: serializes model objects to CSV format."""

import csv
import sys

from reddipy.exporters.base import BaseExporter


class CSVExporter(BaseExporter):
    def export(self, data: list, output_path: str | None = None) -> None:
        """Export data as CSV.

        Args:
            data: List of Post, Comment, or UserActivity objects.
            output_path: File path to write to. If None, writes to stdout.
        """
        if not data:
            return

        rows = [item.to_dict() for item in data]

        # Detect if these are comment dicts (they have a 'replies' key)
        if "replies" in rows[0]:
            rows = self._flatten_comments(rows)

        if not rows:
            return

        fieldnames = list(rows[0].keys())

        if output_path is not None:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        else:
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _flatten_comments(self, data: list[dict]) -> list[dict]:
        """Recursively flatten nested comment replies into a flat list.

        Removes the 'replies' key from each row so CSV columns stay uniform.
        Depth and parent_id are retained in each row to preserve hierarchy.

        Args:
            data: List of comment dicts (each may contain a 'replies' list).

        Returns:
            Flat list of comment dicts with 'replies' key removed.
        """
        result: list[dict] = []
        for comment in data:
            replies = comment.pop("replies", [])
            result.append(comment)
            if replies:
                result.extend(self._flatten_comments(replies))
        return result
