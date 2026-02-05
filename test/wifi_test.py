"""
WiFi Manager Comprehensive Test Suite

This script systematically tests all functions and features available in the
WifiManager class. Each test is clearly labeled and demonstrates different
WiFi and network capabilities.

Author: Aiden Cherniske
Date: 2026-01-30
"""

import time
import gc

from wifiFunctions import WifiManager


# Test configuration
PAUSE_BETWEEN_TESTS = 2.0  # seconds between tests

# Test URLs and endpoints
TEST_URLS = {
    'json_api': 'https://jsonplaceholder.typicode.com/todos/1',
    'http_test': 'http://httpbin.org/get',
    'https_test': 'https://httpbin.org/get',
    'large_response': 'https://jsonplaceholder.typicode.com/posts',
    'user_agent': 'https://httpbin.org/user-agent',
    'headers': 'https://httpbin.org/headers',
    'post_test': 'https://httpbin.org/post',
}


def print_test_header(test_name, description=""):
    """Print a formatted test header."""
    print("\n" + "=" * 60)
    print(f"TEST: {test_name}")
    if description:
        print(f"Description: {description}")
    print("=" * 60)


def pause(duration=None):
    """Pause for a specified duration."""
    duration = duration or PAUSE_BETWEEN_TESTS
    time.sleep(duration)


def print_memory_info():
    """Print current memory usage."""
    gc.collect()
    free = gc.mem_free()
    allocated = gc.mem_alloc()
    total = free + allocated
    print(f"  Memory: {allocated} bytes used, {free} bytes free ({(allocated/total)*100:.1f}% used)")


def test_initialization():
    """Test WiFi manager initialization."""
    print_test_header("WiFi Initialization", "Initialize and connect to WiFi")
    
    try:
        wifi = WifiManager(verbose=False, auto_connect=True)
        print("  ✓ WiFi initialized and connected successfully")
        return wifi
    except Exception as e:
        print(f"  ✗ WiFi initialization failed: {e}")
        return None


def test_connection_status(wifi):
    """Test connection status reporting."""
    print_test_header("Connection Status", "Check WiFi connection state")
    
    print(f"  Connected: {wifi.connected}")
    print(f"  IP Address: {wifi.ip_address}")
    mac_str = ':'.join(wifi.mac_address)
    print(f"  MAC Address: {mac_str}")
    print(f"  Signal Strength: {wifi.signal_strength} dBm")
    
    print("\n  Getting detailed status...")
    status = wifi.get_status()
    for key, value in status.items():
        print(f"    {key}: {value}")
    
    print("\n  Formatted status output:")
    wifi.print_status()
    
    print("  ✓ Connection status test complete")
    pause()


def test_basic_ping(wifi):
    """Test basic ping functionality."""
    print_test_header("Basic Ping", "Test connectivity with ICMP ping")
    
    test_hosts = [
        ("Google DNS", wifi.GOOGLE_DNS),
        ("Cloudflare DNS", wifi.CLOUDFLARE_DNS),
    ]
    
    for name, host in test_hosts:
        print(f"  Pinging {name} ({host})...")
        try:
            ping_time = wifi.ping(host, count=3)
            if ping_time is not None:
                print(f"    ✓ Average ping time: {ping_time:.2f} ms")
            else:
                print(f"    ✗ Ping failed (timeout)")
        except Exception as e:
            print(f"    ✗ Ping error: {e}")
        print()
    
    print("  ✓ Basic ping test complete")
    pause()


def test_simple_get_request(wifi):
    """Test simple HTTP GET request."""
    print_test_header("Simple GET Request", "Fetch data from test API")
    
    url = TEST_URLS['json_api']
    print(f"  Requesting: {url}")
    
    try:
        response = wifi.get(url)
        print(f"  ✓ Status Code: {response.status_code}")
        print(f"  Response Text: {response.text[:100]}...")
        response.close()
        print("  ✓ Simple GET request successful")
    except Exception as e:
        print(f"  ✗ GET request failed: {e}")
    
    print_memory_info()
    pause()


def test_json_parsing(wifi):
    """Test JSON response parsing."""
    print_test_header("JSON Parsing", "Parse JSON from API response")
    
    url = TEST_URLS['json_api']
    print(f"  Requesting: {url}")
    
    try:
        data = wifi.fetch_json(url)
        print("  ✓ JSON parsed successfully")
        print(f"  Data type: {type(data)}")
        print("  JSON content:")
        for key, value in data.items():
            print(f"    {key}: {value}")
        print("  ✓ JSON parsing test successful")
    except Exception as e:
        print(f"  ✗ JSON parsing failed: {e}")
    
    print_memory_info()
    pause()


def test_http_vs_https(wifi):
    """Test both HTTP and HTTPS requests."""
    print_test_header("HTTP vs HTTPS", "Test both protocols")
    
    protocols = [
        ("HTTP", TEST_URLS['http_test']),
        ("HTTPS", TEST_URLS['https_test']),
    ]
    
    for name, url in protocols:
        print(f"  Testing {name}: {url}")
        try:
            response = wifi.get(url, timeout=15)
            print(f"    ✓ Status Code: {response.status_code}")
            text_len = len(response.text)
            print(f"    Response length: {text_len} bytes")
            response.close()
        except Exception as e:
            print(f"    ✗ {name} request failed: {e}")
        print()
    
    print("  ✓ HTTP/HTTPS test complete")
    print_memory_info()
    pause()


def test_custom_headers(wifi):
    """Test requests with custom headers."""
    print_test_header("Custom Headers", "Send requests with custom HTTP headers")
    
    url = TEST_URLS['headers']
    print(f"  Requesting: {url}")
    
    custom_headers = {
        'X-Custom-Header': 'TestValue123',
        'X-API-Key': 'dummy-api-key',
        'User-Agent': 'CircuitPython-Test/1.0'
    }
    
    print("  Custom headers:")
    for key, value in custom_headers.items():
        print(f"    {key}: {value}")
    
    try:
        response = wifi.get(url, headers=custom_headers)
        print(f"  ✓ Status Code: {response.status_code}")
        
        # Parse response to see our headers echoed back
        data = response.json()
        print("\n  Server saw these headers:")
        for key, value in data.get('headers', {}).items():
            print(f"    {key}: {value}")
        
        response.close()
        print("\n  ✓ Custom headers test successful")
    except Exception as e:
        print(f"  ✗ Custom headers test failed: {e}")
    
    print_memory_info()
    pause()


def test_post_request(wifi):
    """Test HTTP POST request."""
    print_test_header("POST Request", "Send data via POST")
    
    url = TEST_URLS['post_test']
    print(f"  Posting to: {url}")
    
    # Test with form data
    print("\n  Test 1: Form data POST")
    form_data = {
        'field1': 'value1',
        'field2': 'value2',
        'timestamp': str(time.monotonic())
    }
    
    try:
        response = wifi.post(url, data=form_data)
        print(f"  ✓ Status Code: {response.status_code}")
        text_len = len(response.text)
        print(f"  Response length: {text_len} bytes")
        response.close()
        print("  ✓ Form data POST successful")
    except Exception as e:
        print(f"  ✗ Form data POST failed: {e}")
    
    print("\n  Test 2: JSON POST")
    json_data = {
        'sensor': 'temperature',
        'value': 23.5,
        'unit': 'celsius'
    }
    
    try:
        response = wifi.post(url, json=json_data)
        print(f"  ✓ Status Code: {response.status_code}")
        text_len = len(response.text)
        print(f"  Response length: {text_len} bytes")
        response.close()
        print("  ✓ JSON POST successful")
    except Exception as e:
        print(f"  ✗ JSON POST failed: {e}")
    
    print_memory_info()
    pause()


def test_timeout_handling(wifi):
    """Test request timeout handling."""
    print_test_header("Timeout Handling", "Test request timeouts")
    
    url = TEST_URLS['json_api']
    
    print("  Test 1: Very short timeout (should timeout)")
    try:
        response = wifi.get(url, timeout=0.001)
        print(f"  Unexpected success: {response.status_code}")
        response.close()
    except Exception as e:
        error_type = type(e).__name__
        print(f"  ✓ Timeout handled correctly: {error_type}")
    
    print("\n  Test 2: Reasonable timeout (should succeed)")
    try:
        response = wifi.get(url, timeout=30)
        print(f"  ✓ Request succeeded: {response.status_code}")
        response.close()
    except Exception as e:
        print(f"  ✗ Request failed: {e}")
    
    print("\n  ✓ Timeout handling test complete")
    print_memory_info()
    pause()


def test_multiple_sequential_requests(wifi):
    """Test multiple sequential requests."""
    print_test_header("Sequential Requests", "Multiple requests in sequence")
    
    url = TEST_URLS['json_api']
    num_requests = 5
    
    print(f"  Making {num_requests} sequential requests...")
    
    success_count = 0
    total_time = 0
    
    for i in range(num_requests):
        try:
            start = time.monotonic()
            response = wifi.get(url)
            elapsed = time.monotonic() - start
            
            print(f"  Request {i+1}/{num_requests}: Status {response.status_code}, {elapsed:.2f}s")
            response.close()
            
            success_count += 1
            total_time += elapsed
            
            # Small delay between requests
            time.sleep(0.5)
        except Exception as e:
            print(f"  Request {i+1}/{num_requests} failed: {e}")
    
    print(f"\n  ✓ {success_count}/{num_requests} requests successful")
    if success_count > 0:
        print(f"  Average request time: {total_time/success_count:.2f}s")
    
    print_memory_info()
    pause()


def test_large_response(wifi):
    """Test handling of large responses."""
    print_test_header("Large Response", "Handle larger API responses")
    
    url = TEST_URLS['large_response']
    print(f"  Requesting large dataset: {url}")
    
    try:
        start = time.monotonic()
        response = wifi.get(url, timeout=30)
        elapsed = time.monotonic() - start
        
        print(f"  ✓ Status Code: {response.status_code}")
        text_len = len(response.text)
        print(f"  Response size: {text_len} bytes")
        print(f"  Request time: {elapsed:.2f}s")
        
        # Try to parse as JSON
        try:
            data = response.json()
            text_len = len(data)
            print(f"  ✓ Parsed {text_len} items from JSON")
        except:
            print("  Could not parse response as JSON")
        
        response.close()
        print("  ✓ Large response test successful")
    except Exception as e:
        print(f"  ✗ Large response test failed: {e}")
    
    print_memory_info()
    pause()


def test_ntp_time(wifi):
    """Test NTP time synchronization."""
    print_test_header("NTP Time Sync", "Get current time from NTP server")
    
    try:
        print("  Requesting UTC time from NTP server...")
        utc_time = wifi.utc_time
        
        print(f"  ✓ UTC Time: {utc_time}")
        print(f"  Year: {utc_time.tm_year}")
        print(f"  Month: {utc_time.tm_mon}")
        print(f"  Day: {utc_time.tm_mday}")
        print(f"  Hour: {utc_time.tm_hour}")
        print(f"  Minute: {utc_time.tm_min}")
        print(f"  Second: {utc_time.tm_sec}")
        
        print("\n  ✓ NTP time sync successful")
    except Exception as e:
        print(f"  ✗ NTP time sync failed: {e}")
    
    pause()


def test_error_handling(wifi):
    """Test error handling for various failure scenarios."""
    print_test_header("Error Handling", "Test handling of various error conditions")
    
    print("  Test 1: Invalid URL")
    try:
        response = wifi.get("http://this-domain-does-not-exist-12345.com")
        print(f"  Unexpected success: {response.status_code}")
        response.close()
    except Exception as e:
        error_type = type(e).__name__
        print(f"  ✓ Error handled: {error_type}")
    
    print("\n  Test 2: Malformed URL")
    try:
        response = wifi.get("not-a-valid-url")
        print(f"  Unexpected success: {response.status_code}")
        response.close()
    except Exception as e:
        error_type = type(e).__name__
        print(f"  ✓ Error handled: {error_type}")
    
    print("\n  Test 3: 404 Not Found")
    try:
        response = wifi.get("https://httpbin.org/status/404")
        print(f"  ✓ Got expected 404: {response.status_code}")
        response.close()
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n  ✓ Error handling test complete")
    print_memory_info()
    pause()


def test_properties_and_methods(wifi):
    """Test WiFi properties and accessor methods."""
    print_test_header("Properties & Methods", "Test property accessors")
    
    print("  Properties:")
    print(f"    connected: {wifi.connected}")
    mac_str = ':'.join(wifi.mac_address)
    print(f"    mac_address: {mac_str}")
    print(f"    ip_address: {wifi.ip_address}")
    print(f"    signal_strength: {wifi.signal_strength} dBm")
    
    print("\n  Direct object access:")
    print(f"    pool: {wifi.pool}")
    print(f"    requests: {wifi.requests}")
    print(f"    ntp: {wifi.ntp}")
    
    print("\n  ✓ Properties test complete")
    pause()


def test_reconnection(wifi):
    """Test WiFi reconnection."""
    print_test_header("Reconnection", "Test disconnect and reconnect")
    
    print("  Initial connection status:")
    print(f"    Connected: {wifi.connected}")
    print(f"    IP: {wifi.ip_address}")
    
    print("\n  Disconnecting...")
    wifi.disconnect()
    time.sleep(2)
    print(f"    Connected: {wifi.connected}")
    
    print("\n  Reconnecting...")
    success = wifi.reconnect()
    time.sleep(2)
    
    if success:
        print("  ✓ Reconnection successful")
        print(f"    Connected: {wifi.connected}")
        print(f"    IP: {wifi.ip_address}")
    else:
        print("  ✗ Reconnection failed")
    
    pause()


def run_all_tests(wifi):
    """Run all WiFi tests in sequence."""
    tests = [
        test_connection_status,
        test_basic_ping,
        test_simple_get_request,
        test_json_parsing,
        test_http_vs_https,
        test_custom_headers,
        test_post_request,
        test_timeout_handling,
        test_multiple_sequential_requests,
        test_large_response,
        test_ntp_time,
        test_error_handling,
        test_properties_and_methods,
        test_reconnection,
    ]
    
    total_tests = len(tests)
    
    for i, test_func in enumerate(tests, 1):
        print(f"\n{'#' * 60}")
        print(f"Running test {i}/{total_tests}")
        print(f"{'#' * 60}")
        
        try:
            test_func(wifi)
            gc.collect()  # Collect garbage between tests
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user.")
            raise
        except Exception as e:
            print(f"\nERROR in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            pause(3.0)


def main():
    """Main test execution."""
    print("\n" + "#" * 60)
    print("WiFi Manager Comprehensive Test Suite")
    print("#" * 60)
    print(f"Pause between tests: {PAUSE_BETWEEN_TESTS}s")
    print("#" * 60)
    
    print("\nNote: This test requires internet connectivity and will")
    print("make multiple HTTP/HTTPS requests to test endpoints.")
    print("Ensure your settings.toml has valid WiFi credentials.")
    print("#" * 60)
    
    # Initialize WiFi
    wifi = test_initialization()
    if wifi is None:
        print("\nFailed to initialize WiFi. Exiting.")
        print("Check your settings.toml file for valid credentials:")
        print("  CIRCUITPY_WIFI_SSID = 'your-network-name'")
        print("  CIRCUITPY_WIFI_PASSWORD = 'your-password'")
        return
    
    # Run all tests
    try:
        run_all_tests(wifi)
        
        print("\n" + "#" * 60)
        print("All tests completed successfully!")
        print("#" * 60)
        
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user.")
    except Exception as e:
        print(f"\n\nTest suite error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nFinal memory status:")
        print_memory_info()


if __name__ == "__main__":
    main()