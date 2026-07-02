"""JSON exporter: serializes model objects to JSON format."""

import json
import sys

from redminer.exporters.base import BaseExporter


class JSONExporter(BaseExporter):
    def export(self, data: list, output_path: str | None = None) -> None:
        """Export data as JSON.

        Args:
            data: List of Post, Comment, or UserActivity objects.
            output_path: File path to write to. If None, prints to stdout.
        """
        serialized = [item.to_dict() for item in data]
        output = json.dumps(serialized, indent=2)

        if output_path is not None:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output)
