"""DizoClip application package."""

__all__ = ["MainWindow"]


def __getattr__(name):
    if name == "MainWindow":
        from app.window.main_window import MainWindow
        return MainWindow
    raise AttributeError(name)
