from abc import ABC, abstractmethod


class SurfaceAdapter(ABC):

    @abstractmethod
    def navigate(self, url: str):
        pass

    @abstractmethod
    def fill(self, selector: str, value: str):
        pass

    @abstractmethod
    def click(self, selector: str):
        pass

    @abstractmethod
    def read_text(self, selector: str) -> str:
        pass

    @abstractmethod
    def screenshot(self, path: str):
        pass

    @abstractmethod
    def close(self):
        pass