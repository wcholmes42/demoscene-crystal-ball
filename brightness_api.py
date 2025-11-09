import screen_brightness_control as sbc
import time
import threading
import subprocess
import sys

class BrightnessController:
    """API for controlling screen brightness"""
    
    def __init__(self):
        self.original_brightness = self.get_brightness()
        print(f"[BRIGHTNESS] Original brightness: {self.original_brightness}%")
    
    def get_brightness(self):
        """Get current brightness (0-100)"""
        try:
            return sbc.get_brightness()[0]  # Returns list, take first monitor
        except Exception as e:
            print(f"[BRIGHTNESS] Error getting brightness: {e}")
            return 100
    
    def set_brightness(self, level):
        """Set brightness (0-100)"""
        try:
            level = max(0, min(100, level))  # Clamp to 0-100
            sbc.set_brightness(level)
            return True
        except Exception as e:
            print(f"[BRIGHTNESS] Error setting brightness: {e}")
            return False
    
    def fade_to(self, target, duration=1.0, steps=10):
        """Smoothly fade to target brightness"""
        current = self.get_brightness()
        step_size = (target - current) / steps
        step_duration = duration / steps
        
        for i in range(steps):
            new_level = current + (step_size * (i + 1))
            self.set_brightness(int(new_level))
            time.sleep(step_duration)
        
    def restore(self):
        """Restore original brightness"""
        print(f"[BRIGHTNESS] Restoring to {self.original_brightness}%")
        self.set_brightness(self.original_brightness)

def brightness_cycle_test():
    """
    Brightness test: Decrease 5% every 5 seconds to 0%, then increase back
    """
    controller = BrightnessController()
    
    print("\n" + "="*60)
    print("BRIGHTNESS CYCLE TEST")
    print("="*60)
    print("Will decrease brightness 5% every 5 seconds until 0%")
    print("Then increase 5% every 5 seconds back to 100%")
    print("="*60 + "\n")
    
    try:
        # PHASE 1: Decrease to 0%
        print("[PHASE 1] DIMMING...")
        for brightness in range(100, -5, -5):  # 100, 95, 90, ..., 5, 0
            controller.set_brightness(brightness)
            print(f"[BRIGHTNESS] Set to {brightness}%")
            time.sleep(5)
        
        # PHASE 2: Increase to 100%
        print("\n[PHASE 2] BRIGHTENING...")
        for brightness in range(5, 105, 5):  # 5, 10, 15, ..., 95, 100
            controller.set_brightness(brightness)
            print(f"[BRIGHTNESS] Set to {brightness}%")
            time.sleep(5)
        
        print("\n[COMPLETE] Brightness cycle complete!")
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopping brightness cycle...")
    finally:
        controller.restore()

def run_demo_with_brightness():
    """
    Launch the crystal ball demo and run brightness cycle in background
    """
    controller = BrightnessController()
    
    print("\n" + "="*60)
    print("DEMOSCENE CRYSTAL BALL + BRIGHTNESS CONTROL")
    print("="*60)
    print("Starting demo with live brightness control...")
    print("Demo will run while brightness cycles")
    print("Press CTRL+C to stop both")
    print("="*60 + "\n")
    
    # Start demo in subprocess
    demo_process = subprocess.Popen(
        [sys.executable, "crystal_ball_demo.py"],
        cwd="C:\\code\\demoscene-crystal-ball"
    )
    
    print("[DEMO] Started with PID:", demo_process.pid)
    time.sleep(3)  # Give demo time to initialize
    
    try:
        # Run brightness cycle in this thread
        brightness_cycle_test()
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopping...")
    finally:
        # Cleanup
        print("[CLEANUP] Terminating demo...")
        demo_process.terminate()
        try:
            demo_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            demo_process.kill()
        
        controller.restore()
        print("[COMPLETE] Demo and brightness control stopped.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Brightness control for demoscene demo")
    parser.add_argument("--test-only", action="store_true", 
                       help="Run brightness cycle test without demo")
    parser.add_argument("--with-demo", action="store_true",
                       help="Run demo with brightness cycle")
    
    args = parser.parse_args()
    
    if args.with_demo:
        run_demo_with_brightness()
    elif args.test_only:
        brightness_cycle_test()
    else:
        # Default: show menu
        print("\nBrightness Control API")
        print("="*40)
        print("1. Test brightness cycle only")
        print("2. Run demo with brightness cycle")
        print("3. Exit")
        choice = input("\nChoice: ")
        
        if choice == "1":
            brightness_cycle_test()
        elif choice == "2":
            run_demo_with_brightness()
        else:
            print("Exiting.")
