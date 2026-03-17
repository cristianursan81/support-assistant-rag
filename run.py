#!/usr/bin/env python3
"""Entry point for the AI Agent Company dashboard."""
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from src.app import main

if __name__ == "__main__":
    main()
