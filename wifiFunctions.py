'''
Author: Matt Lamparter
Updated 2024.12.13

A basic set of functions to connect to WiFi using an ESP32-S3 Feather
This is based on the guide from Adafruit:
https://learn.adafruit.com/adafruit-esp32-s3-feather/circuitpython-internet-test

You'll need to edit the settings.toml file on the root of your CIRCUITPY drive
update the variables CIRCUITPY_WIFI_SSID and CIRCUITPY_WIFI_PASSWORD

Updated 2025.04.30
The api_get() function now supports passing the "headers" parameter to adafruit_requests.Session().get()
The headers parameter is optional and may be left out, as we traditionally did for API requests such as those
used for timeapi.io:  api_get('https://www.timeapi.io/api/time/current/ip?ipAddress=237.71.232.203')

Alternatively, if an API request requires passing a header with an API key, that functionality is now supported.
Such an example would be:
api_get('https://api.api-ninjas.com/v1/exercises?type=cardio', headersInput={'X-Api-Key': 'your_API_key_here'})

Updated 2025.11.07
Tired of failing free API time sources, this library was switched to use the adafruit_ntp library
This library relies on an Adafruit-hosted NTP server.  This server returns UTC time so the end
users is required to update the time for their local timezone.
'''
import os
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests
import adafruit_ntp



class wifiObject():


    def __init__(self, verbose=0):
        #self.__debug = debug
        self.__verbose = verbose
        self.__MAC = [hex(i) for i in wifi.radio.mac_address]
        self.__IPv4 = wifi.radio.ipv4_address
        self.__pool = socketpool.SocketPool(wifi.radio)
        self.__requests = adafruit_requests.Session(self.__pool, ssl.create_default_context())
        self.__ntp = adafruit_ntp.NTP(self.__pool, tz_offset=0, cache_seconds=3600)

        print("ESP32-S3 WebClient Test")
        print(f"My MAC address: {[hex(i) for i in wifi.radio.mac_address]}")
        if(verbose == 1):
            print("Available WiFi networks:")
            for network in wifi.radio.start_scanning_networks():
                print("\t%s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
                                                 network.rssi, network.channel))
            wifi.radio.stop_scanning_networks()

        print(f"Connecting to {os.getenv('CIRCUITPY_WIFI_SSID')}")
        wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
        print(f"Connected to {os.getenv('CIRCUITPY_WIFI_SSID')}")
        print(f"My IP address: {wifi.radio.ipv4_address}")

        ping_ip = ipaddress.IPv4Address("8.8.8.8")
        ping = wifi.radio.ping(ip=ping_ip)
        # retry once if timed out
        if ping is None:
            ping = wifi.radio.ping(ip=ping_ip)
        if ping is None:
            print("Couldn't ping 'google.com' successfully")
        else:
            # convert s to ms
            print(f"Pinging 'google.com' took: {ping * 1000} ms")

    def getPool(self):
        return self.__pool

    def getNTP(self):
        return self.__ntp

    def getRequests(self):
        return self.__requests
    
    def getUTC(self):
        ntp = self.getNTP()
        return ntp.datetime

    def getMAC(self):
        return self.__MAC

    def getIP(self):
        return self.__IPv4

    def api_get(self, URL, headersInput=None):
        # Some API providers require the use of the 'headers' argument for storing an API key
        # this argument is optional
        if headersInput == None:
            response = self.__requests.get(URL)
        if headersInput != None:
            response = self.__requests.get(URL, headers=headersInput)
        # if the URL is identified as a ThingSpeak write, check to see if "0" is
        # returned.  A 0 signifies a write failure.  In that case, notify
        # the user.
        if URL.find('api.thingspeak.com/update') != -1:
            if int(response.text) == 0:
                print('ThingSpeak write failed.  Check channel ID, API write key, etc.')
                print('Also remember that for free ThingSpeak channels you can only write data once every 15 seconds.')
                print('For details check out:  https://thingspeak.mathworks.com/pages/license_faq')
        return response
