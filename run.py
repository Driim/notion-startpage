#!/usr/bin/env python
"""Convenience script to run StartPage application."""
import asyncio
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from startpage.startpage import main

if __name__ == "__main__":
    asyncio.run(main())
