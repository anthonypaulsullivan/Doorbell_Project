import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wifi_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Try importing required packages with error handling
required_packages = {
    'pywifi': None,
    'tkinter': None,
    'pyttsx3': None,
    'sqlite3': None
}

for package in required_packages:
    try:
        if package == 'tkinter':
            import tkinter as tk
            from tkinter import simpledialog
            required_packages[package] = tk
        elif package == 'pywifi':
            import pywifi
            required_packages[package] = pywifi
        elif package == 'pyttsx3':
            import pyttsx3
            required_packages[package] = pyttsx3
        elif package == 'sqlite3':
            import sqlite3
            required_packages[package] = sqlite3
        
        logging.info(f"Successfully imported {package}")
    except ImportError as e:
        logging.error(f"Failed to import {package}. Error: {str(e)}")
        print(f"\nError: The required package '{package}' is not installed.")
        print(f"Please install it using: pip install {package}")
        if package == 'pywifi':
            print("\nNote: For pywifi on Windows, you might also need to:")
            print("1. Install Visual C++ build tools")
            print("2. Run: pip install comtypes")
        sys.exit(1)

import time
import json
import threading
from pathlib import Path

class WifiMonitor:
    def __init__(self):
        logging.info("Initializing WifiMonitor")
        try:
            self.wifi = pywifi.PyWiFi()
            self.iface = self.wifi.interfaces()[0]
            logging.info(f"Successfully initialized WiFi interface: {self.iface.name()}")
        except Exception as e:
            logging.error(f"Failed to initialize WiFi interface: {str(e)}")
            raise

        self.known_networks = {}
        self.db_path = Path("wifi_networks.db")
        self.setup_database()
        self.load_known_networks()
        
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            logging.info("Successfully initialized text-to-speech engine")
        except Exception as e:
            logging.error(f"Failed to initialize text-to-speech: {str(e)}")
            raise

    def setup_database(self):
        """Initialize SQLite database for storing network information."""
        logging.info("Setting up database")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS networks (
                    bssid TEXT PRIMARY KEY,
                    ssid TEXT,
                    custom_name TEXT,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            logging.info("Database setup successful")
        except Exception as e:
            logging.error(f"Database setup failed: {str(e)}")
            raise

    def load_known_networks(self):
        """Load known networks from database."""
        logging.info("Loading known networks")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT bssid, ssid, custom_name FROM networks")
            for row in cursor.fetchall():
                self.known_networks[row[0]] = {
                    'ssid': row[1],
                    'custom_name': row[2]
                }
            conn.close()
            logging.info(f"Loaded {len(self.known_networks)} known networks")
        except Exception as e:
            logging.error(f"Failed to load known networks: {str(e)}")
            raise

    def prompt_for_name(self, ssid, bssid):
        """Prompt user to name a new network."""
        logging.info(f"Prompting for name for network: {ssid}")
        try:
            root = tk.Tk()
            root.withdraw()
            custom_name = simpledialog.askstring(
                "New Network Detected",
                f"New network detected: {ssid}\nEnter a custom name for this network:",
                parent=root
            )
            
            if custom_name:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO networks 
                    (bssid, ssid, custom_name, first_seen, last_seen) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (bssid, ssid, custom_name, now, now)
                )
                conn.commit()
                conn.close()
                self.known_networks[bssid] = {
                    'ssid': ssid,
                    'custom_name': custom_name
                }
                logging.info(f"Network named: {custom_name}")
            root.destroy()
            return custom_name
        except Exception as e:
            logging.error(f"Failed to prompt for network name: {str(e)}")
            return None

    def announce_network(self, message):
        """Announce network using text-to-speech."""
        logging.info(f"Announcing: {message}")
        try:
            self.tts_engine.say(message)
            self.tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"Failed to announce message: {str(e)}")

    def scan_networks(self):
        """Scan for WiFi networks."""
        logging.info("Scanning for networks")
        try:
            self.iface.scan()
            time.sleep(2)  # Wait for scan to complete
            results = self.iface.scan_results()
            logging.info(f"Found {len(results)} networks")
            return results
        except Exception as e:
            logging.error(f"Network scan failed: {str(e)}")
            return []

    def monitor(self):
        """Main monitoring loop."""
        logging.info("Starting WiFi monitoring...")
        print("\nWiFi Monitor is running. Check the system tray icon.")
        print("Monitoring for new networks...\n")
        
        while True:
            try:
                networks = self.scan_networks()
                
                for network in networks:
                    bssid = network.bssid
                    ssid = network.ssid
                    
                    if not ssid:  # Skip networks with empty SSIDs
                        continue
                        
                    if bssid not in self.known_networks:
                        print(f"\nNew network detected: {ssid}")
                        logging.info(f"New network detected: {ssid}")
                        self.announce_network("New signal detected")
                        
                        custom_name = self.prompt_for_name(ssid, bssid)
                        
                        if custom_name:
                            self.announce_network(f"Network named {custom_name}")
                    else:
                        custom_name = self.known_networks[bssid]['custom_name']
                        if custom_name:
                            print(f"Detected known network: {custom_name} ({ssid})")
                            self.announce_network(f"Detected {custom_name}")
                
                time.sleep(10)  # Wait before next scan
                
            except Exception as e:
                logging.error(f"Error during monitoring: {str(e)}")
                time.sleep(5)  # Wait before retrying

def create_system_tray(root):
    """Create system tray icon and menu."""
    try:
        import pystray
        from PIL import Image, ImageDraw

        # Create a simple icon
        icon_size = 64
        icon_image = Image.new('RGB', (icon_size, icon_size), 'blue')
        draw = ImageDraw.Draw(icon_image)
        draw.ellipse([icon_size/4, icon_size/4, 3*icon_size/4, 3*icon_size/4], fill='white')

        def on_exit(icon):
            icon.stop()
            root.quit()

        menu = pystray.Menu(
            pystray.MenuItem("Exit", on_exit)
        )

        icon = pystray.Icon(
            "wifi_monitor",
            icon_image,
            "WiFi Monitor",
            menu
        )

        return icon

    except ImportError:
        logging.warning("pystray not installed, running without system tray icon")
        return None

def main():
    try:
        monitor = WifiMonitor()
        
        # Create a thread for monitoring
        monitor_thread = threading.Thread(target=monitor.monitor, daemon=True)
        monitor_thread.start()
        
        # Create main window (hidden)
        root = tk.Tk()
        root.withdraw()
        
        # Create system tray icon
        icon = create_system_tray(root)
        
        if icon:
            icon.run()
        else:
            root.mainloop()

    except Exception as e:
        logging.error(f"Application failed to start: {str(e)}")
        print(f"\nError: {str(e)}")
        print("Check wifi_monitor.log for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
