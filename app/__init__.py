"""DizoClip application package."""
__version__ = "1.1.0"

__all__ = ["MainWindow", "__version__"]


def __getattr__(name):
    if name == "MainWindow":
        from app.window.main_window import MainWindow
        return MainWindow
    raise AttributeError(name)
