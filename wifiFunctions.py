"""
Author: Matt Lamparter
Updated 2024.12.13
Refactored by Aiden Cherniske 2026.01.28

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


class WifiManager:
    """
    Manages WiFi connectivity and network operations for ESP32-S3.
    
    Automatically connects to WiFi on initialization and provides
    access to HTTP requests and NTP time synchronization.
    """
    
    # Constants
    GOOGLE_DNS = "8.8.8.8"
    CLOUDFLARE_DNS = "1.1.1.1"

    THINGSPEAK_UPDATE_URL = "api.thingspeak.com/update"
    THINGSPEAK_MIN_INTERVAL = 15  # Seconds between free tier writes

    # NTP constants
    DEFAULT_NTP_TZ_OFFSET = -5  # US Eastern Time
    DEFAULT_NTP_CACHE_SECONDS = 3600  # 1 hour
    
    def __init__(self, verbose=False, auto_connect=True):
        """
        Initialize WiFi connection and network services.
        
        Args:
            verbose: If True, print available WiFi networks during scan
        """
        self._verbose = verbose
        self._connected = False

        self._mac = None
        self._ipv4 = None
        self._pool = None
        self._requests = None
        self._ntp = None

        if auto_connect:
            self.connect()

    @property
    def connected(self):
        """Check if device is connected to WiFi."""
        return self._connected and wifi.radio.connected

    @property
    def mac_address(self):
        """Get device MAC address as hex string list."""
        if self._mac is None:
            self._mac = [f"{b:02X}" for b in wifi.radio.mac_address]
        return self._mac

    @property
    def ip_address(self):
        """Get device IPv4 address."""
        return wifi.radio.ipv4_address if self.connected else None

    @property
    def signal_strength(self):
        """Get WiFi signal strength (RSSI) in dBm."""
        return wifi.radio.ap_rssi if self.connected else None

    @property
    def pool(self):
        """Get socket pool for network operations."""
        return self._pool

    @property
    def requests(self):
        """Get requests session for HTTP operations."""
        return self._requests

    @property
    def ntp(self):
        """Get NTP client for time synchronization."""
        return self._ntp

    @property
    def utc_time(self):
        """Get current UTC time from NTP server."""
        if self._ntp is None:
            raise RuntimeError("NTP client not initialized")
        return self._ntp.datetime

    def connect(self):
        """
        Connect to WiFi network.
        
        Args:
            ssid: Network SSID (default: from settings.toml)
            password: Network password (default: from settings.toml)
            
        Returns:
            bool: True if connection successful
        """
        print("ESP32-S3 Wifi Manager")
        print("======================")
        print(f"MAC address: {self.mac_address}")

        if self._verbose:
            self._scan_networks()

        # Get credentials
        ssid = ssid or os.getenv("CIRCUITPY_WIFI_SSID")
        password = password or os.getenv("CIRCUITPY_WIFI_PASSWORD")

        if not ssid or not password:
            raise ValueError("WiFi SSID and password must be set in settings.toml")
        
        # Connect to WiFi
        print(f"Connecting to {ssid}...")
        try:
            wifi.radio.connect(ssid, password)
            self._connected = True
            print(f"Connected to {ssid}")
            print(f"IP address: {self.ip_address}")
            
            # Initialize network services
            self._initialize_services()
            
            # Test connectivity
            self._test_connectivity()
            
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """Disconnect from WiFi network."""
        if self.connected:
            wifi.radio.enabled = False
            wifi.radio.enabled = True
            self._connected = False
            print("Disconnected from WiFi")

    def reconnect(self):
        """Reconnect to WiFi using stored credentials."""
        self.disconnect()
        return self.connect()

    def _initialize_services(self):
        """Initialize network services (socket pool, requests, NTP)."""
        self._pool = socketpool.SocketPool(wifi.radio)
        self._requests = adafruit_requests.Session(
            self._pool, 
            ssl.create_default_context()
        )
        self._ntp = adafruit_ntp.NTP(
            self._pool, 
            tz_offset=self.DEFAULT_NTP_TZ_OFFSET, 
            cache_seconds=self.DEFAULT_NTP_CACHE_SECONDS
        )

    def _scan_networks(self):
        """Scan and display available WiFi networks."""
        print("Available WiFi networks:")
        try:
            for network in wifi.radio.start_scanning_networks():
                print(f"\t{network.ssid}\t\tRSSI: {network.rssi}\tChannel: {network.channel}")
            wifi.radio.stop_scanning_networks()
        except Exception as e:
            print(f"Network scan failed: {e}")

    def _test_connectivity(self, test_ip=None):
        """
        Test internet connectivity by pinging a DNS server.
        
        Args:
            test_ip: IP address to ping (default: Google DNS)
        """
        test_ip = test_ip or self.GOOGLE_DNS
        ping_ip = ipaddress.IPv4Address(test_ip)
        ping = wifi.radio.ping(ip=ping_ip)
        
        # Retry once if timeout
        if ping is None:
            ping = wifi.radio.ping(ip=ping_ip)
        
        if ping is None:
            print(f"Warning: Could not ping {test_ip}")
        else:
            print(f"Ping to {test_ip}: {ping * 1000:.2f} ms")

    def get(self, url, header=None, timeout=10):
        """
        Perform HTTP GET request.
        
        Args:
            url: API endpoint URL
            headers: Optional dict of HTTP headers (e.g., {'X-Api-Key': 'key'})
            timeout: Request timeout in seconds (default: 10)
            
        Returns:
            Response: HTTP response object
            
        Raises:
            RuntimeError: If not connected to WiFi
            
        Examples:
            # Simple GET request
            response = wifi.get('https://api.example.com/data')
            
            # With API key header
            response = wifi.get(
                'https://api.example.com/data',
                headers={'X-Api-Key': 'your_key'}
            )
        """
        if not self.connected:
            raise RuntimeError("Not connected to WiFi. Call connect() first.")
        
        response = self._requests.get(url, headers=headers, timeout=timeout)
        
        # Validate ThingSpeak writes if applicable
        if self.THINGSPEAK_UPDATE_URL in url:
            self._validate_thingspeak_response(response)
        
        return response

    def post(self, url, data=None, json=None, headers=None, timeout=10):
        """
        Perform HTTP POST request.
        
        Args:
            url: API endpoint URL
            data: Form data to send
            json: JSON data to send
            headers: Optional dict of HTTP headers
            timeout: Request timeout in seconds (default: 10)
            
        Returns:
            Response: HTTP response object
            
        Raises:
            RuntimeError: If not connected to WiFi
        """
        if not self.connected:
            raise RuntimeError("Not connected to WiFi. Call connect() first.")
        
        return self._requests.post(url, data=data, json=json, headers=headers, timeout=timeout)

    def _validate_thingspeak_response(self, response):
        """
        Validate ThingSpeak API response for write failures.
        
        Args:
            response: HTTP response from ThingSpeak update
        """
        try:
            if int(response.text) == 0:
                self._print_thingspeak_error()
        except ValueError:
            # Response wasn't a number, which is also an error
            self._print_thingspeak_error()

    def _print_thingspeak_error(self):
        """Print formatted ThingSpeak error message."""
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

    def fetch_json(self, url, headers=None):
        """
        Fetch and parse JSON from a URL.
        
        Args:
            url: URL to fetch
            headers: Optional HTTP headers
            
        Returns:
            dict: Parsed JSON data
            
        Raises:
            RuntimeError: If not connected to WiFi
            ValueError: If response is not valid JSON
        """
        response = self.get(url, headers=headers)
        return response.json()

    def ping(self, host=None, count=1):
        """
        Ping a host to test connectivity.
        
        Args:
            host: IP address or hostname to ping (default: Google DNS)
            count: Number of ping attempts (default: 1)
            
        Returns:
            float: Average ping time in milliseconds, or None if all pings failed
        """
        host = host or self.GOOGLE_DNS
        
        if isinstance(host, str) and not host.replace('.', '').isdigit():
            # Host is a hostname, not an IP - would need DNS lookup
            print(f"Warning: Hostname resolution not implemented. Using {self.GOOGLE_DNS}")
            host = self.GOOGLE_DNS
        
        ping_ip = ipaddress.IPv4Address(host)
        total_time = 0
        successful_pings = 0
        
        for _ in range(count):
            ping_time = wifi.radio.ping(ip=ping_ip)
            if ping_time is not None:
                total_time += ping_time
                successful_pings += 1
        
        if successful_pings == 0:
            return None
        
        avg_time_ms = (total_time / successful_pings) * 1000
        return avg_time_ms

    def get_status(self):
        """
        Get comprehensive WiFi status information.
        
        Returns:
            dict: Status information including connection state, IP, signal strength, etc.
        """
        return {
            'connected': self.connected,
            'ssid': wifi.radio.ap_info.ssid if self.connected else None,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'mac_address': ':'.join(self.mac_address),
            'signal_strength': self.signal_strength,
            'channel': wifi.radio.ap_info.channel if self.connected else None,
        }

    def print_status(self):
        """Print formatted WiFi status information."""
        status = self.get_status()
        
        print("=" * 60)
        print("WiFi Status")
        print("=" * 60)
        print(f"Connected:       {status['connected']}")
        print(f"SSID:            {status['ssid'] or 'N/A'}")
        print(f"IP Address:      {status['ip_address'] or 'N/A'}")
        print(f"MAC Address:     {status['mac_address']}")
        print(f"Signal Strength: {status['signal_strength']} dBm" if status['signal_strength'] else "Signal Strength: N/A")
        print(f"Channel:         {status['channel'] or 'N/A'}")
        print("=" * 60)

# Backwards compatibility - Global instance management
_global_wifi = None

def _get_global_wifi():
    """Get or create the global WiFi instance."""
    global _global_wifi
    if _global_wifi is None:
        _global_wifi = WiFiManager()
    return _global_wifi


# Backwards compatibility functions (matching old API)
class wifiObject(WifiManager):
    """Backwards compatibility alias for WiFiManager."""
    
    def __init__(self, verbose=False):
        """Initialize with old-style parameters."""
        super().__init__(verbose=verbose, auto_connect=True)
    
    def get_pool(self):
        """Deprecated: Use pool property instead."""
        return self.pool
    
    def get_ntp(self):
        """Deprecated: Use ntp property instead."""
        return self.ntp
    
    def get_requests(self):
        """Deprecated: Use requests property instead."""
        return self.requests
    
    def get_utc(self):
        """Deprecated: Use utc_time property instead."""
        return self.utc_time
    
    def get_mac(self):
        """Deprecated: Use mac_address property instead."""
        return self.mac_address
    
    def get_ip(self):
        """Deprecated: Use ip_address property instead."""
        return self.ip_address
    
    def api_get(self, url, headers=None):
        """Deprecated: Use get() method instead."""
        return self.get(url, headers=headers)