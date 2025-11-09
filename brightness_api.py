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
    Brightness test: FAST continuous fade 100% → 0% → 100% repeating
    """
    controller = BrightnessController()
    
    print("\n" + "="*60)
    print("BRIGHTNESS CYCLE TEST - FAST CONTINUOUS FADING")
    print("="*60)
    print("Rapidly fading 100% → BLACK (0%) → 100% with no pauses")
    print("5 seconds per direction, 10 second full cycle")
    print("Press CTRL+C to stop")
    print("="*60 + "\n")
    
    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            print(f"\n[CYCLE {cycle_count}] Dimming to BLACK...")
            
            # Fast fade to BLACK
            for current in range(100, -1, -1):
                controller.set_brightness(current)
                print(f"[BRIGHTNESS] {current}%", end="\r")
                time.sleep(0.05)  # 50ms = FAST!
            
            # Ensure absolute BLACK
            controller.set_brightness(0)
            
            print(f"\n[CYCLE {cycle_count}] Brightening from BLACK...")
            
            # Fast fade from BLACK
            for current in range(0, 101):
                controller.set_brightness(current)
                print(f"[BRIGHTNESS] {current}%", end="\r")
                time.sleep(0.05)  # 50ms = FAST!
            
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
        """Background thread for FAST CONTINUOUS brightness cycling with DEBUG"""
        print("[BRIGHTNESS] *** Worker thread STARTED ***")
        try:
            cycle = 0
            while not stop_brightness.is_set():
                cycle += 1
                print(f"\n[BRIGHTNESS] === CYCLE {cycle} === Dimming to BLACK...")
                
                # PHASE 1: Fast fade to BLACK (0%)
                for current in range(100, -1, -1):
                    if stop_brightness.is_set():
                        break
                    result = controller.set_brightness(current)
                    if current % 20 == 0:  # Debug every 20%
                        actual = controller.get_brightness()
                        print(f"[BRIGHTNESS] Set:{current}% Actual:{actual}% OK:{result}")
                    time.sleep(0.05)  # 50ms per step = 5 second fade
                
                controller.set_brightness(0)
                print(f"[BRIGHTNESS] === DARKEST === 0%")
                
                if stop_brightness.is_set():
                    break
                
                print(f"[BRIGHTNESS] === CYCLE {cycle} === Brightening from BLACK...")
                
                # PHASE 2: Fast fade from black to bright
                for current in range(0, 101):
                    if stop_brightness.is_set():
                        break
                    result = controller.set_brightness(current)
                    if current % 20 == 0:  # Debug every 20%
                        actual = controller.get_brightness()
                        print(f"[BRIGHTNESS] Set:{current}% Actual:{actual}% OK:{result}")
                    time.sleep(0.05)  # 50ms per step = 5 second fade
                
                print(f"[BRIGHTNESS] === BRIGHTEST === 100%")
                # Loop immediately
                
        except Exception as e:
            print(f"[BRIGHTNESS] Error: {e}")
        finally:
            print("[BRIGHTNESS] Thread stopping, restoring brightness...")
            controller.restore()
    
    print("\n" + "="*60)
    print("DEMOSCENE CRYSTAL BALL + FAST BRIGHTNESS CONTROL")
    print("="*60)
    print("Starting demo with FAST brightness cycling...")
    print("Fades to absolute BLACK and back every 10 seconds")
    print("Photos change every 3 seconds")
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
