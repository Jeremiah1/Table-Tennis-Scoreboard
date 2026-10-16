import os
import sys

# The modules under test live in src/, which is the root of CIRCUITPY on device.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
