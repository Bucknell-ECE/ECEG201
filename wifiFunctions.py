"""
Author: Matt Lamparter
Updated 2024.12.13
Refactored by Aiden Cherniske 2026.01.23

WiFi connectivity and API request management for ESP32-S3 Feather.

Based on Adafruit guide:
https://learn.adafruit.com/adafruit-esp32-s3-feather/circuitpython-internet-test

Setup:
- Edit settings.toml on CIRCUITPY drive
- Set CIRCUITPY_WIFI_SSID and CIRCUITPY_WIFI_PASSWORD

Features:
- WiFi connection management
- HTTP/HTTPS requests with optional headers
- NTP time synchronization (UTC)
- ThingSpeak API support with validation
"""

import os
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests
import adafruit_ntp


class WiFiObject:
    """
    Manages WiFi connectivity and network operations for ESP32-S3.
    
    Automatically connects to WiFi on initialization and provides
    access to HTTP requests and NTP time synchronization.
    """
    
    # Constants
    GOOGLE_DNS = "8.8.8.8"
    THINGSPEAK_UPDATE_URL = "api.thingspeak.com/update"
    THINGSPEAK_MIN_INTERVAL = 15  # Seconds between free tier writes
    
    def __init__(self, verbose=False):
        """
        Initialize WiFi connection and network services.
        
        Args:
            verbose: If True, print available WiFi networks during scan
        """
        self._verbose = verbose
        self._mac = [hex(i) for i in wifi.radio.mac_address]
        self._ipv4 = wifi.radio.ipv4_address
        
        # Network setup
        self._pool = socketpool.SocketPool(wifi.radio)
        self._requests = adafruit_requests.Session(
            self._pool, 
            ssl.create_default_context()
        )
        self._ntp = adafruit_ntp.NTP(
            self._pool, 
            tz_offset=0, 
            cache_seconds=3600
        )
        
        self._connect_to_wifi()
        self._test_connectivity()

    def _connect_to_wifi(self):
        """Establish WiFi connection using credentials from settings.toml."""
        print("ESP32-S3 WebClient Test")
        print(f"MAC address: {self._mac}")
        
        if self._verbose:
            self._scan_networks()
        
        ssid = os.getenv("CIRCUITPY_WIFI_SSID")
        password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
        
        print(f"Connecting to {ssid}...")
        wifi.radio.connect(ssid, password)
        print(f"Connected to {ssid}")
        print(f"IP address: {wifi.radio.ipv4_address}")

    def _scan_networks(self):
        """Scan and display available WiFi networks."""
        print("Available WiFi networks:")
        for network in wifi.radio.start_scanning_networks():
            print(f"\t{network.ssid}\t\tRSSI: {network.rssi}\tChannel: {network.channel}")
        wifi.radio.stop_scanning_networks()

    def _test_connectivity(self):
        """Test internet connectivity by pinging Google DNS."""
        ping_ip = ipaddress.IPv4Address(self.GOOGLE_DNS)
        ping = wifi.radio.ping(ip=ping_ip)
        
        # Retry once if timeout
        if ping is None:
            ping = wifi.radio.ping(ip=ping_ip)
        
        if ping is None:
            print(f"Warning: Could not ping {self.GOOGLE_DNS}")
        else:
            print(f"Ping to {self.GOOGLE_DNS}: {ping * 1000:.2f} ms")

    def get_pool(self):
        """
        Get the socket pool for network operations.
        
        Returns:
            SocketPool: Network socket pool instance
        """
        return self._pool

    def get_ntp(self):
        """
        Get the NTP client for time synchronization.
        
        Returns:
            NTP: Adafruit NTP client instance
        """
        return self._ntp
    def get_requests(self):
        """
        Get the requests session for HTTP operations.
        
        Returns:
            Session: Adafruit requests session instance
        """
        return self._requests

    def get_utc(self):
        """
        Get current UTC time from NTP server.
        
        Returns:
            time.struct_time: Current UTC time
        """
        return self._ntp.datetime

    def get_mac(self):
        """
        Get device MAC address.
        
        Returns:
            list: MAC address bytes as hex strings
        """
        return self._mac

    def get_ip(self):
        """
        Get device IPv4 address.
        
        Returns:
            IPv4Address: Current IP address
        """
        return self._ipv4

    def api_get(self, url, headers=None):
        """
        Perform HTTP GET request to an API endpoint.
        
        Automatically detects and validates ThingSpeak write operations.
        
        Args:
            url: API endpoint URL
            headers: Optional dict of HTTP headers (e.g., {'X-Api-Key': 'key'})
            
        Returns:
            Response: HTTP response object
            
        Examples:
            # Simple GET request
            response = wifi.api_get('https://api.example.com/data')
            
            # With API key header
            response = wifi.api_get(
                'https://api.example.com/data',
                headers={'X-Api-Key': 'your_key'}
            )
        """
        # Make request with or without headers
        response = self._requests.get(url, headers=headers) if headers else self._requests.get(url)
        
        # Validate ThingSpeak writes
        if self.THINGSPEAK_UPDATE_URL in url:
            self._check_thingspeak_response(response)
        
        return response

    def _check_thingspeak_response(self, response):
        """
        Check ThingSpeak API response for write failures.
        
        Args:
            response: HTTP response from ThingSpeak update
        """
        if int(response.text) == 0:
            print("=" * 60)
            print("ThingSpeak write FAILED")
            print("=" * 60)
            print("Common issues:")
            print("  - Incorrect channel ID or API write key")
            print(f"  - Free tier: max 1 write per {self.THINGSPEAK_MIN_INTERVAL} seconds")
            print("  - Channel may be full or disabled")
            print()
            print("Details: https://thingspeak.mathworks.com/pages/license_faq")
            print("=" * 60)