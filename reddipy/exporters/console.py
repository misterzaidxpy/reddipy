"""Console exporter: prints rich formatted tables to stdout."""

from rich.console import Console
from rich.table import Table

from reddipy.exporters.base import BaseExporter


def _truncate(text: str | None, max_len: int) -> str:
    if text is None:
        return ""
    text = text.replace("\n", " ").replace("\r", "")
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


class ConsoleExporter(BaseExporter):
    def export(self, data: list, output_path: str | None = None) -> None:
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

    def _print_posts(self, data: list) -> None:
        table = Table(show_header=True, header_style="bold cyan", border_style="dim",
                      pad_edge=False, show_lines=False, expand=True)
        table.add_column("ID", style="dim", no_wrap=True, ratio=1)
        table.add_column("Title", ratio=5)
        table.add_column("Author", style="green", ratio=2)
        table.add_column("Subreddit", style="magenta", ratio=2)
        table.add_column("Score", justify="right", style="yellow", ratio=1)
        table.add_column("Comments", justify="right", style="blue", ratio=1)

        for item in data:
            table.add_row(
                item.id,
                _truncate(item.title, 62),
                item.author,
                f"r/{item.subreddit}",
                str(item.score),
                str(item.num_comments),
            )

        Console().print(table)

    def _print_comments(self, data: list) -> None:
        table = Table(show_header=True, header_style="bold cyan", border_style="dim",
                      pad_edge=False, show_lines=False, expand=True)
        table.add_column("ID", style="dim", no_wrap=True, ratio=1)
        table.add_column("Author", style="green", ratio=2)
        table.add_column("Comment", ratio=5)
        table.add_column("Score", justify="right", style="yellow", ratio=1)
        table.add_column("Depth", justify="right", style="blue", ratio=1)

        for item in data:
            table.add_row(
                item.id,
                item.author,
                _truncate(item.body, 52),
                str(item.score),
                str(item.depth),
            )

        Console().print(table)

    def _print_user_activity(self, data: list) -> None:
        table = Table(show_header=True, header_style="bold cyan", border_style="dim",
                      pad_edge=False, show_lines=False, expand=True)
        table.add_column("Type", style="bold", ratio=1)
        table.add_column("ID", style="dim", no_wrap=True, ratio=1)
        table.add_column("Author", style="green", ratio=2)
        table.add_column("Subreddit", style="magenta", ratio=2)
        table.add_column("Score", justify="right", style="yellow", ratio=1)
        table.add_column("Content", ratio=4)

        for item in data:
            content = item.title if item.title is not None else item.body
            table.add_row(
                item.type,
                item.id,
                item.author,
                f"r/{item.subreddit}",
                str(item.score),
                _truncate(content, 47),
            )

        Console().print(table)
