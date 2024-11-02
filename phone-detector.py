#!/usr/bin/env python3
import subprocess
import time
import pyttsx3
from datetime import datetime

class WifiPhoneDetector:
    def __init__(self):
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        
        # Set of known networks and their last seen time
        self.known_networks = {}
        
        # Set voice properties for better announcements
        voices = self.tts_engine.getProperty('voices')
        self.tts_engine.setProperty('rate', 150)    # Slower speaking rate
        # Try to use a female voice if available
        for voice in voices:
            if "female" in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
    
    def announce(self, message):
        """Announce message using text-to-speech"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
        self.tts_engine.say(message)
        self.tts_engine.runAndWait()
    
    def get_networks(self):
        """Get list of currently visible WiFi networks with signal strength"""
        try:
            # Run netsh command to get wireless networks with more details
            output = subprocess.check_output(
                ['netsh', 'wlan', 'show', 'networks', 'mode=Bssid'], 
                universal_newlines=True
            )
            
            networks = {}
            current_ssid = None
            
            # Parse the output to get SSIDs and signal strength
            for line in output.split('\n'):
                if 'SSID' in line and 'BSSID' not in line:
                    ssid = line.split(':')[-1].strip()
                    if ssid and ssid != '':
                        current_ssid = ssid
                        networks[ssid] = {'signal': 0, 'first_seen': datetime.now()}
                elif 'Signal' in line and current_ssid:
                    signal = int(line.split(':')[-1].strip().replace('%', ''))
                    networks[current_ssid]['signal'] = signal
            
            return networks
            
        except subprocess.CalledProcessError as e:
            print(f"Error scanning networks: {e}")
            return {}
    
    def analyze_network_changes(self, current_networks):
        """Analyze changes in network visibility"""
        timestamp = datetime.now()
        
        # Check for new or stronger networks
        for ssid, data in current_networks.items():
            if ssid not in self.known_networks:
                # New network appeared
                if data['signal'] > 60:  # Strong signal suggests very close proximity
                    self.announce(f"New device detected very close by with signal strength {data['signal']}%")
                else:
                    self.announce(f"New device detected with signal strength {data['signal']}%")
                self.known_networks[ssid] = data
            else:
                # Check for significant signal strength increase
                old_signal = self.known_networks[ssid]['signal']
                new_signal = data['signal']
                if new_signal > old_signal + 20:  # Signal increased by more than 20%
                    self.announce(f"Device {ssid} moving closer. Signal increased from {old_signal}% to {new_signal}%")
                
                self.known_networks[ssid]['signal'] = new_signal
        
        # Check for networks that disappeared
        for ssid in list(self.known_networks.keys()):
            if ssid not in current_networks:
                self.announce(f"Device {ssid} moved out of range")
                del self.known_networks[ssid]

    def start_monitoring(self, interval=10):
        """Start continuous monitoring"""
        self.announce("Starting phone detection monitoring")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        try:
            while True:
                current_networks = self.get_networks()
                self.analyze_network_changes(current_networks)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.tts_engine.stop()

if __name__ == "__main__":
    detector = WifiPhoneDetector()
    # Scan every 10 seconds
    detector.start_monitoring(interval=10)
