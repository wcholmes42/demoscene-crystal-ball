"""
Quick launcher for demoscene demo with brightness control

Usage:
    python run_demo_test.py          # Interactive menu
    python run_demo_test.py --test   # Brightness test only
    python run_demo_test.py --full   # Demo + brightness
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brightness_api import brightness_cycle_test, run_demo_with_brightness

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if "--test" in sys.argv:
            print("Running brightness cycle test only...")
            brightness_cycle_test()
        elif "--full" in sys.argv:
            print("Running demo with brightness control...")
            run_demo_with_brightness()
        else:
            print("Usage: python run_demo_test.py [--test|--full]")
    else:
        print("\n🔮 DEMOSCENE CRYSTAL BALL - BRIGHTNESS TEST 💡")
        print("="*50)
        print()
        print("This will dim your screen from 100% → 0%")
        print("Then brighten from 0% → 100%")
        print("5% change every 5 seconds")
        print()
        print("Press ENTER to start (CTRL+C to stop anytime)")
        input()
        
        run_demo_with_brightness()
