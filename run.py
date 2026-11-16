"""Entry point for PyInstaller and for `python run.py`."""
import sys

from promethea.handoff import try_handoff

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--word-export":
        from promethea.word_export import main as word_export
        sys.exit(word_export(sys.argv[2:]))
    if try_handoff(sys.argv):
        sys.exit(0)
    from promethea.app import main
    sys.exit(main())
