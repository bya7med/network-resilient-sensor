"""Wi-Fi as the upload code sees it.

Tests and the drop script flip this. On a Pi this would follow the real link.
"""


class Link:
    def __init__(self, up: bool = True) -> None:
        self._up = up

    def is_up(self) -> bool:
        return self._up

    def drop(self) -> None:
        self._up = False

    def reconnect(self) -> None:
        self._up = True
