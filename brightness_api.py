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
    Brightness test: CONTINUOUS smooth fade 100% → 0% → 100% repeating
    """
    controller = BrightnessController()
    
    print("\n" + "="*60)
    print("BRIGHTNESS CYCLE TEST - CONTINUOUS SMOOTH FADING")
    print("="*60)
    print("Continuously fading 100% → 0% → 100% with no pauses")
    print("Press CTRL+C to stop")
    print("="*60 + "\n")
    
    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            print(f"\n[CYCLE {cycle_count}] Dimming 100% → 0%...")
            
            # Dim from 100 to 0
            for current in range(100, -1, -1):
                controller.set_brightness(current)
                print(f"[BRIGHTNESS] {current}%", end="\r")
                time.sleep(0.1)
            
            print(f"\n[CYCLE {cycle_count}] Brightening 0% → 100%...")
            
            # Brighten from 0 to 100
            for current in range(0, 101):
                controller.set_brightness(current)
                print(f"[BRIGHTNESS] {current}%", end="\r")
                time.sleep(0.1)
            
            print()  # New line after cycle
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopping brightness cycle...")
    finally:
        controller.restore()

def run_demo_with_brightness():
    """
    Launch the crystal ball demo and run SMOOTH brightness cycle in background thread
    """
    controller = BrightnessController()
    stop_brightness = threading.Event()
    
    def brightness_worker():
        """Background thread for CONTINUOUS smooth brightness cycling"""
        try:
            while not stop_brightness.is_set():
                # PHASE 1: Smooth dim from 100% to 0%
                for current in range(100, -1, -1):
                    if stop_brightness.is_set():
                        break
                    controller.set_brightness(current)
                    time.sleep(0.1)  # 100ms per step = 10 second fade
                
                if stop_brightness.is_set():
                    break
                
                # PHASE 2: Smooth brighten from 0% to 100%
                for current in range(0, 101):
                    if stop_brightness.is_set():
                        break
                    controller.set_brightness(current)
                    time.sleep(0.1)  # 100ms per step = 10 second fade
                
                # Loop immediately, no pause
                
        except Exception as e:
            print(f"[BRIGHTNESS] Error: {e}")
        finally:
            print("[BRIGHTNESS] Thread stopping, restoring brightness...")
            controller.restore()
    
    print("\n" + "="*60)
    print("DEMOSCENE CRYSTAL BALL + SMOOTH BRIGHTNESS CONTROL")
    print("="*60)
    print("Starting demo with smooth brightness cycling...")
    print("Press ESC in demo window to exit")
    print("="*60 + "\n")
    
    # Start brightness thread
    brightness_thread = threading.Thread(target=brightness_worker, daemon=True)
    brightness_thread.start()
    print("[BRIGHTNESS] Smooth animation thread started")
    
    # Start demo in subprocess
    demo_process = subprocess.Popen(
        [sys.executable, "crystal_ball_demo.py"],
        cwd="C:\\code\\demoscene-crystal-ball"
    )
    
    print(f"[DEMO] Started with PID: {demo_process.pid}")
    
    try:
        # Wait for demo to finish
        demo_process.wait()
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopping...")
        demo_process.terminate()
        
    finally:
        # CRITICAL: Stop brightness thread and restore
        print("[CLEANUP] Stopping brightness control...")
        stop_brightness.set()
        brightness_thread.join(timeout=2)
        
        # Ensure demo is dead
        if demo_process.poll() is None:
            print("[CLEANUP] Terminating demo...")
            demo_process.terminate()
            try:
                demo_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                demo_process.kill()
        
        # Final restore
        controller.restore()
        print("[COMPLETE] Demo and brightness control stopped. Brightness restored.")

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
