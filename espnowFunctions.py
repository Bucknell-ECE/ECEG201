"""
Author: Aiden Cherniske
Written: 2025.10.15
Refactored: 2026.01.23

ESP-NOW communication management for ESP32-S3.

Based on Adafruit guide:
https://learn.adafruit.com/esp-now-in-circuitpython

Requirements:
- ESP32-S3 board with CircuitPython
- Adafruit CircuitPython Bundle libraries:
  - asyncio
  - adafruit_ticks

Features:
- Flexible MAC address input formats
- Asynchronous send/receive
- Automatic peer management
"""

import board
import wifi
import espnow
import time

try:
    import asyncio
except ImportError:
    raise ImportError(
        "This code requires the asyncio library. "
        "Please install it from the Adafruit CircuitPython Bundle."
    )

try:
    import adafruit_ticks
except ImportError:
    raise ImportError(
        "This code requires the adafruit_ticks library. "
        "Please install it from the Adafruit CircuitPython Bundle."
    )


class ESPNowManager:
    """
    Manages ESP-NOW communication with an ESP32-S3.
    
    Allows adding/removing peers, sending, and receiving messages asynchronously.
    Supports multiple MAC address formats for convenience.
    """
    
    def __init__(self):
        """Initialize ESP-NOW manager."""
        self._espnow = None
        self._peers = {}  # Dictionary to store peers with MAC as key
        self._loop = asyncio.get_event_loop()
    
    @staticmethod
    def mac_to_bytes(mac):
        """
        Convert MAC address from hex string to bytes.
        
        Accepts formats:
        - '24:6F:28:AB:CD:EF'
        - '24-6F-28-AB-CD-EF'
        - '246F28ABCDEF'
        - bytes object: b'\\x24\\x6F\\x28\\xAB\\xCD\\xEF'
        
        Args:
            mac: MAC address as string or bytes
            
        Returns:
            bytes: MAC address as bytes
        """
        if isinstance(mac, bytes):
            return mac
        
        # Remove separators
        mac = mac.replace(':', '').replace('-', '').replace(' ', '')
        
        return bytes.fromhex(mac)
    
    @staticmethod
    def mac_to_str(mac_bytes):
        """
        Convert MAC bytes to readable string format.
        
        Args:
            mac_bytes: MAC address as bytes
            
        Returns:
            str: MAC address as colon-separated hex string
        """
        return ':'.join(f'{b:02x}' for b in mac_bytes)
    
    def start(self):
        """Start ESP-NOW communication."""
        wifi.radio.enabled = True
        self._espnow = espnow.ESPNow()
        print("ESP-NOW started")
    
    def stop(self):
        """Stop ESP-NOW communication."""
        if self._espnow:
            self._espnow.deinit()
            print("ESP-NOW stopped")
    
    def add_peer(self, mac):
        """
        Add a peer for ESP-NOW communication.
        
        Args:
            mac: Peer MAC address (string or bytes)
        """
        mac_bytes = self.mac_to_bytes(mac)
        
        if mac_bytes in self._peers:
            print(f"Peer {self.mac_to_str(mac_bytes)} already exists")
            return
        
        try:
            peer = espnow.Peer(mac=mac_bytes)
            self._espnow.peers.append(peer)
            self._peers[mac_bytes] = peer
            print(f"Peer {self.mac_to_str(mac_bytes)} added")
        except Exception as e:
            print(f"Error: Failed to add peer: {e}")
    
    def remove_peer(self, mac):
        """
        Remove a peer from ESP-NOW communication.
        
        Args:
            mac: Peer MAC address (string or bytes)
        """
        mac_bytes = self.mac_to_bytes(mac)
        
        if mac_bytes not in self._peers:
            print(f"Peer {self.mac_to_str(mac_bytes)} not found")
            return
        
        try:
            peer = self._peers[mac_bytes]
            self._espnow.peers.remove(peer)
            del self._peers[mac_bytes]
            print(f"Peer {self.mac_to_str(mac_bytes)} removed")
        except Exception as e:
            print(f"Error: Failed to remove peer: {e}")
    
    def send_message(self, mac, message):
        """
        Send a message to a peer.
        
        Note: This is synchronous. ESP-NOW send operation is inherently blocking.
        
        Args:
            mac: Peer MAC address (string or bytes)
            message: Message to send (bytes)
        """
        mac_bytes = self.mac_to_bytes(mac)
        
        if mac_bytes not in self._peers:
            print(f"Error: Peer {self.mac_to_str(mac_bytes)} not found")
            return
        
        try:
            peer = self._peers[mac_bytes]
            self._espnow.send(message, peer)
            print(f"Message sent to {self.mac_to_str(mac_bytes)}: {message}")
        except Exception as e:
            print(f"Error: Failed to send message: {e}")
    
    async def receive_messages(self):
        """
        Continuously receive messages from peers.
        
        This is an async coroutine that runs in the event loop.
        """
        while True:
            packet = self._espnow.read()
            if packet:
                mac = packet.mac
                msg = packet.msg
                print(f"Message received from {self.mac_to_str(mac)}: {msg}")
            await asyncio.sleep(0.1)