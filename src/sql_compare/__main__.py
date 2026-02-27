# -*- coding: utf-8 -*-
"""
Main entry point for the application.
"""
import sys
from .cli import parse_args, run_cli
from .gui import launch_gui

def main():
    args = parse_args(sys.argv[1:])

    if args.web:
        from .web import app
        # In production this entry point might not be used, but for local testing:
        app.run(debug=True, port=5000)
        return

    # If no files/strings/stdin provided and not web, try to launch GUI
    if not args.files and not args.strings and not args.stdin:
        launch_gui()
    else:
        run_cli(args)

if __name__ == "__main__":
    main()
