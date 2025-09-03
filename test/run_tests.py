#!/usr/bin/env python3
"""
Test Runner for AI Motor Monitoring System
Runs both ESP and PLC simulators simultaneously
"""

import time
import threading
import subprocess
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self):
        self.esp_process = None
        self.plc_process = None
        self.running = False
    
    def start_esp_simulator(self, server_url="http://localhost:5000", interval=5):
        """Start ESP simulator in separate process"""
        try:
            cmd = [
                sys.executable, "tests/esp_simulator.py",
                "--server", server_url,
                "--interval", str(interval)
            ]
            
            self.esp_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            logger.info("🔌 ESP Simulator started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start ESP simulator: {e}")
            return False
    
    def start_plc_simulator(self, plc_ip="192.168.3.39", plc_port=5007, interval=10):
        """Start PLC simulator in separate process"""
        try:
            cmd = [
                sys.executable, "tests/plc_simulator.py",
                "--ip", plc_ip,
                "--port", str(plc_port),
                "--interval", str(interval)
            ]
            
            self.plc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            logger.info("🏭 PLC Simulator started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start PLC simulator: {e}")
            return False
    
    def run_combined_test(self, duration=300):
        """Run both simulators for specified duration"""
        logger.info("🚀 Starting Combined Test Suite")
        logger.info(f"⏱️  Duration: {duration} seconds")
        logger.info("📊 Expected values: 24V, 6.25A, 2650 RPM, ~28°C")
        
        # Start both simulators
        esp_ok = self.start_esp_simulator(interval=5)
        time.sleep(2)  # Brief delay
        plc_ok = self.start_plc_simulator(interval=10)
        
        if not (esp_ok and plc_ok):
            logger.error("Failed to start simulators")
            self.stop_all()
            return
        
        self.running = True
        start_time = time.time()
        
        try:
            # Monitor for specified duration
            while self.running and (time.time() - start_time) < duration:
                time.sleep(5)
                
                # Check if processes are still running
                if self.esp_process and self.esp_process.poll() is not None:
                    logger.warning("ESP simulator stopped unexpectedly")
                
                if self.plc_process and self.plc_process.poll() is not None:
                    logger.warning("PLC simulator stopped unexpectedly")
            
            logger.info("✅ Test completed successfully")
            
        except KeyboardInterrupt:
            logger.info("🛑 Test interrupted by user")
        
        finally:
            self.stop_all()
    
    def stop_all(self):
        """Stop all running simulators"""
        self.running = False
        
        if self.esp_process:
            self.esp_process.terminate()
            try:
                self.esp_process.wait(timeout=5)
                logger.info("🔌 ESP Simulator stopped")
            except subprocess.TimeoutExpired:
                self.esp_process.kill()
                logger.warning("🔌 ESP Simulator force killed")
        
        if self.plc_process:
            self.plc_process.terminate()
            try:
                self.plc_process.wait(timeout=5)
                logger.info("🏭 PLC Simulator stopped")
            except subprocess.TimeoutExpired:
                self.plc_process.kill()
                logger.warning("🏭 PLC Simulator force killed")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Runner for Motor Monitoring System')
    parser.add_argument('--duration', type=int, default=300,
                       help='Test duration in seconds (default: 300)')
    parser.add_argument('--server', default='http://localhost:5000',
                       help='Server URL for ESP simulator')
    parser.add_argument('--plc-ip', default='192.168.3.39',
                       help='PLC IP address')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    print("=" * 60)
    print("🧪 AI MOTOR MONITORING SYSTEM - TEST SUITE")
    print("=" * 60)
    print(f"🌐 Server: {args.server}")
    print(f"🏭 PLC: {args.plc_ip}:5007") 
    print(f"⏱️  Duration: {args.duration} seconds")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print()
    
    runner.run_combined_test(args.duration)

if __name__ == "__main__":
    main()
