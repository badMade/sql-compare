#!/bin/bash
# Wrapper script to run Tkinter tests headlessly using xvfb-run
xvfb-run python -m unittest discover -s tests -p "test_gui.py"
