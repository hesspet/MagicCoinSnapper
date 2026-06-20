from __future__ import annotations

import sys
from typing import Optional, Sequence


def _create_app(argv: Optional[Sequence[str]] = None):
    from PySide6.QtWidgets import QApplication

    return QApplication(list(argv) if argv is not None else sys.argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Startet die MagicCoinSnapper Trainer GUI."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "GUI-Abhaengigkeiten fehlen. Installiere mit: pip install -e .[gui]",
            file=sys.stderr,
        )
        return 1

    args = list(argv) if argv is not None else sys.argv
    dataset_path: Optional[str] = None
    if "--dataset" in args:
        i = args.index("--dataset")
        if i + 1 < len(args):
            dataset_path = args[i + 1]

    app = QApplication(args if argv is not None else sys.argv)
    from mcs_trainer.app.main_window import MainWindow

    window = MainWindow()
    if dataset_path:
        window.open_dataset_path(dataset_path)
    window.show()
    return app.exec()


def gui(argv: Optional[Sequence[str]] = None) -> int:
    """Entry-Point fuer den CLI-Befehl `mcs-trainer gui`."""
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
