"""
Author: Aiden Cherniske
Written: 2025.10.15

A basic set of functions to manage ESP-NOW communication using an ESP32-S3

This is based on the guide from Adafruit:
https://learn.adafruit.com/esp-now-in-circuitpython

You will need to have the ESP32-S3 board set up with CircuitPython and the necessary libraries installed.
From the Adafruit CircuitPython Bundle, you will need:
- Asyncio
- Adafruit Ticks
This code allows for more flexible MAC address input formats and improved peer management.
The MAC address can be provided in the following formats:
- '24:6F:28:AB:CD:EF'
- '24-6F-28-AB-CD-EF'
- '246F28ABCDEF'
- bytes object: b'\x24\x6F\x28\xAB\xCD\xEF'
The code uses asyncio to handle sending and receiving messages concurrently.
"""

import board
import wifi
import espnow
import time

try: #check if asyncio is available
    import asyncio
except ImportError:
    raise ImportError("This code requires the asyncio library. Please install it from the Adafruit CircuitPython Bundle.")

try: #check if adafruit_ticks is available
    import adafruit_ticks
except ImportError:
    raise ImportError("This code requires the adafruit_ticks library. Please install it from the Adafruit CircuitPython Bundle.")

class ESPNowManager:
    """A class to manage ESP-NOW communication with an ESP32-S3
    Allows adding/removing peers, sending, and receiving messages asynchronously.
    """
    def __init__(self):
        self.espnow = None
        self.peers = {}  #dictionary to store peers with MAC as key
        self.loop = asyncio.get_event_loop()
    
    @staticmethod
    def mac_to_bytes(mac):
        """Convert MAC address from hex string to bytes.
        Accepts formats: '24:6F:28:AB:CD:EF', '24-6F-28-AB-CD-EF', '246F28ABCDEF'
        """
        if isinstance(mac, bytes):
            return mac

        mac = mac.replace(':', '').replace('-', '').replace(' ', '') #remove seperators
        

        return bytes.fromhex(mac) #convert to bytes
    
    @staticmethod
    def mac_to_str(mac_bytes):
        """Convert MAC bytes to readable string format."""
        return ':'.join('{:02x}'.format(b) for b in mac_bytes)
    
    def start(self):
        """Start ESP-NOW communication."""
        wifi.radio.enabled = True
        self.espnow = espnow.ESPNow()
        # Remove active() - not needed in CircuitPython
        print("ESPNow started")
    
    def stop(self):
        """Stop ESP-NOW communication."""
        if self.espnow:
            # Use deinit() instead of active(False)
            self.espnow.deinit()
            print("ESPNow stopped")
    
    def add_peer(self, mac):
        """Add a peer for ESP-NOW communication."""
        mac_bytes = self.mac_to_bytes(mac)  #convert to bytes if string
        
        if mac_bytes not in self.peers:
            # Create a Peer object
            peer = espnow.Peer(mac=mac_bytes)
            self.espnow.peers.append(peer)
            self.peers[mac_bytes] = peer  #store the peer object
            print(f"Peer {self.mac_to_str(mac_bytes)} added")
    
    def remove_peer(self, mac):
        mac_bytes = self.mac_to_bytes(mac)  #convert to bytes if string
        
        if mac_bytes in self.peers:  #get the peer object and remove it
            peer = self.peers[mac_bytes]
            self.espnow.peers.remove(peer)
            del self.peers[mac_bytes]
            print(f"Peer {self.mac_to_str(mac_bytes)} removed")
    
    async def send_message(self, mac, message):
        mac_bytes = self.mac_to_bytes(mac)  #convert to bytes if string
        
        if mac_bytes in self.peers:
            peer = self.peers[mac_bytes]  #get the Peer object
            self.espnow.send(message, peer)  #pass Peer object
            print(f"Message sent to {self.mac_to_str(mac_bytes)}: {message}")
        else:
            print(f"Peer {self.mac_to_str(mac_bytes)} not found")
    
    async def receive_messages(self):
        while True:
            packet = self.espnow.read()
            if packet:
                mac = packet.mac
                msg = packet.msg
                print(f"Message received from {self.mac_to_str(mac)}: {msg}")
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    #Example usage of ESPNowManager class
    async def main():
        manager = ESPNowManager()
        manager.start()
        
        peer_mac = 'FF:FF:FF:FF:FF:FF'  #replace with actual peer MAC address
        manager.add_peer(peer_mac)
        
        #run both simultaneously
        await asyncio.gather(
            manager.receive_messages(),
            send_periodically(manager, peer_mac)
        )

    async def send_periodically(manager, mac):
        while True:
            await manager.send_message(mac, b'Ping!')
            await asyncio.sleep(5)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted")
        try:
            manager.stop()
        except NameError:
            pass