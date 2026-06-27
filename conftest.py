import os
import sys

# Ensure the project root is importable so tests can do `from src.utils.utils import ...`
# regardless of pytest's import mode / where it is invoked from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
