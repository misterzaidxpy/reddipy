"""Abstract base class for all exporters."""

from abc import ABC, abstractmethod


class BaseExporter(ABC):
    @abstractmethod
    def export(self, data: list, output_path: str | None = None) -> None:
        pass
