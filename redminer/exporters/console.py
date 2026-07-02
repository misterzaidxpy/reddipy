"""Console exporter: prints a formatted table to stdout."""

from redminer.exporters.base import BaseExporter


def _truncate(text: str | None, max_len: int) -> str:
    """Truncate text to max_len characters, appending '...' if needed."""
    if text is None:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


class ConsoleExporter(BaseExporter):
    def export(self, data: list, output_path: str | None = None) -> None:
        """Print a formatted table to stdout. output_path is ignored.

        Args:
            data: List of Post, Comment, or UserActivity objects.
            output_path: Ignored. Output always goes to stdout.
        """
        if not data:
            return

        first = data[0]
        class_name = type(first).__name__

        if class_name == "Post":
            self._print_posts(data)
        elif class_name == "Comment":
            self._print_comments(data)
        elif class_name == "UserActivity":
            self._print_user_activity(data)
        else:
            # Fallback: use to_dict keys
            rows = [item.to_dict() for item in data]
            headers = list(rows[0].keys())
            self._print_table(headers, [[str(row.get(h, "")) for h in headers] for row in rows])

    # ------------------------------------------------------------------
    # Post table
    # ------------------------------------------------------------------

    def _print_posts(self, data: list) -> None:
        col_widths = {
            "id": 10,
            "title": 63,  # 60 chars + 3 for potential "..."
            "author": 20,
            "subreddit": 20,
            "score": 8,
            "num_comments": 12,
        }
        headers = list(col_widths.keys())
        rows = []
        for item in data:
            rows.append([
                str(item.id),
                _truncate(item.title, 60),
                str(item.author),
                str(item.subreddit),
                str(item.score),
                str(item.num_comments),
            ])
        self._print_table(headers, rows, col_widths)

    # ------------------------------------------------------------------
    # Comment table
    # ------------------------------------------------------------------

    def _print_comments(self, data: list) -> None:
        col_widths = {
            "id": 10,
            "author": 20,
            "body": 53,  # 50 chars + 3 for potential "..."
            "score": 8,
            "depth": 6,
        }
        headers = list(col_widths.keys())
        rows = []
        for item in data:
            rows.append([
                str(item.id),
                str(item.author),
                _truncate(item.body, 50),
                str(item.score),
                str(item.depth),
            ])
        self._print_table(headers, rows, col_widths)

    # ------------------------------------------------------------------
    # UserActivity table
    # ------------------------------------------------------------------

    def _print_user_activity(self, data: list) -> None:
        col_widths = {
            "type": 8,
            "id": 10,
            "author": 20,
            "subreddit": 20,
            "score": 8,
            "title/body": 53,  # 50 chars + 3 for potential "..."
        }
        headers = list(col_widths.keys())
        rows = []
        for item in data:
            content = item.title if item.title is not None else item.body
            rows.append([
                str(item.type),
                str(item.id),
                str(item.author),
                str(item.subreddit),
                str(item.score),
                _truncate(content, 50),
            ])
        self._print_table(headers, rows, col_widths)

    # ------------------------------------------------------------------
    # Generic table printer
    # ------------------------------------------------------------------

    def _print_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        col_widths: dict[str, int] | None = None,
    ) -> None:
        """Print headers and rows with column alignment and a separator line."""
        if col_widths is None:
            # Auto-calculate widths from data
            widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    widths[i] = max(widths[i], len(cell))
            col_widths = {h: widths[i] for i, h in enumerate(headers)}

        widths = [col_widths[h] for h in headers]
        fmt = "  ".join(f"{{:<{w}}}" for w in widths)

        print(fmt.format(*headers))
        print("  ".join("-" * w for w in widths))
        for row in rows:
            # Pad/trim each cell to match the column width
            cells = [str(cell)[:widths[i]] for i, cell in enumerate(row)]
            print(fmt.format(*cells))
