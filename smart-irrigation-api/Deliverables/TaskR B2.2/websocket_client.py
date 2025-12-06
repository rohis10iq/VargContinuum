#!/usr/bin/env python3
"""
WebSocket Client Example - Demonstrates how to connect to the real-time sensor stream
and process incoming sensor data updates.
"""

import asyncio
import json
import websockets
import requests
from datetime import datetime
from typing import Optional


class SensorStreamClient:
    """Client for connecting to real-time sensor data stream."""
    
    def __init__(self, api_url: str = "http://localhost:8000", ws_url: str = "ws://localhost:8000"):
        """
        Initialize the sensor stream client.
        
        Args:
            api_url: Base URL for REST API (for authentication)
            ws_url: Base URL for WebSocket (usually same as api_url)
        """
        self.api_url = api_url
        self.ws_url = ws_url
        self.token: Optional[str] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.sensor_data = {}
        self.is_connected = False
    
    def login(self, username: str, password: str) -> bool:
        """
        Authenticate and get JWT token.
        
        Args:
            username: Username for login
            password: Password for login
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": username, "password": password}
            )
            response.raise_for_status()
            self.token = response.json()["access_token"]
            print(f"✓ Authenticated as {username}")
            return True
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    async def connect(self) -> bool:
        """
        Connect to WebSocket sensor stream.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.token:
            print("✗ Must authenticate first (call login())")
            return False
        
        try:
            uri = f"{self.ws_url}/ws/sensors?token={self.token}"
            self.ws = await websockets.connect(uri)
            self.is_connected = True
            print(f"✓ Connected to sensor stream")
            return True
        except Exception as e:
            print(f"✗ WebSocket connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket stream."""
        if self.ws:
            await self.ws.close()
            self.is_connected = False
            print("✓ Disconnected from sensor stream")
    
    async def receive_updates(self, callback=None):
        """
        Receive sensor updates from stream.
        
        Args:
            callback: Optional async function to call for each update
                     signature: async def callback(message: dict)
        """
        if not self.is_connected:
            print("✗ Not connected. Call connect() first.")
            return
        
        try:
            async for message_text in self.ws:
                message = json.loads(message_text)
                
                if message["type"] == "connection_status":
                    self._handle_connection_status(message)
                elif message["type"] == "sensor_reading":
                    self._handle_sensor_reading(message)
                
                if callback:
                    await callback(message)
        
        except websockets.exceptions.ConnectionClosed:
            print("✓ Connection closed")
        except Exception as e:
            print(f"✗ Error receiving updates: {e}")
    
    def _handle_connection_status(self, message: dict):
        """Handle connection status messages."""
        data = message["data"]
        print(f"\n📊 Connection Status:")
        print(f"   Status: {data['status']}")
        print(f"   Client ID: {data['client_id']}")
        print(f"   Active Clients: {data['active_clients']}")
    
    def _handle_sensor_reading(self, message: dict):
        """Handle sensor reading messages."""
        data = message["data"]
        sensor_id = data["sensor_id"]
        
        # Store sensor data
        self.sensor_data[sensor_id] = {
            "moisture": data.get("moisture"),
            "temperature": data.get("temperature"),
            "humidity": data.get("humidity"),
            "light": data.get("light"),
            "timestamp": message["timestamp"]
        }
        
        # Print update
        timestamp = datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00"))
        print(f"\n🌱 {sensor_id} @ {timestamp.strftime('%H:%M:%S')}")
        
        if data.get("moisture") is not None:
            moisture_level = "🔴" if data["moisture"] < 30 else "🟡" if data["moisture"] < 60 else "🟢"
            print(f"   Moisture: {data['moisture']}% {moisture_level}")
        
        if data.get("temperature") is not None:
            print(f"   Temperature: {data['temperature']}°C")
        
        if data.get("humidity") is not None:
            print(f"   Humidity: {data['humidity']}%")
        
        if data.get("light") is not None:
            print(f"   Light: {data['light']} lux")
    
    def get_latest_reading(self, sensor_id: str) -> Optional[dict]:
        """Get latest reading for a sensor."""
        return self.sensor_data.get(sensor_id)
    
    def get_all_readings(self) -> dict:
        """Get all latest sensor readings."""
        return self.sensor_data.copy()


async def main_loop_mode():
    """Example 1: Continuous loop receiving updates."""
    print("=" * 50)
    print("Example 1: Continuous Loop Mode")
    print("=" * 50)
    
    client = SensorStreamClient()
    
    # Authenticate
    if not client.login("test_user", "test_pass"):
        return
    
    # Connect to stream
    if not await client.connect():
        return
    
    # Receive updates in a loop
    print("\nListening for sensor updates (Press Ctrl+C to stop)...\n")
    
    try:
        await client.receive_updates()
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        await client.disconnect()


async def custom_callback_mode():
    """Example 2: Using a custom callback for each update."""
    print("=" * 50)
    print("Example 2: Custom Callback Mode")
    print("=" * 50)
    
    client = SensorStreamClient()
    
    # Authenticate
    if not client.login("test_user", "test_pass"):
        return
    
    # Connect to stream
    if not await client.connect():
        return
    
    # Define custom callback
    async def process_update(message):
        """Custom callback for processing updates."""
        if message["type"] == "sensor_reading":
            data = message["data"]
            # Could trigger actions here (e.g., start irrigation if moisture < 30%)
            if data.get("moisture") and data["moisture"] < 30:
                print(f"   ⚠️  Low moisture warning for {data['sensor_id']}")
    
    # Receive updates with callback
    print("\nListening for sensor updates with custom callback...\n")
    
    try:
        await client.receive_updates(callback=process_update)
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        await client.disconnect()


async def batch_mode():
    """Example 3: Batch processing mode with time window."""
    print("=" * 50)
    print("Example 3: Batch Processing Mode")
    print("=" * 50)
    
    client = SensorStreamClient()
    
    # Authenticate
    if not client.login("test_user", "test_pass"):
        return
    
    # Connect to stream
    if not await client.connect():
        return
    
    # Receive updates for 30 seconds then display summary
    print("\nCollecting sensor data for 30 seconds...\n")
    
    try:
        # Use a task with timeout
        await asyncio.wait_for(
            client.receive_updates(),
            timeout=30
        )
    except asyncio.TimeoutError:
        pass
    except KeyboardInterrupt:
        print("\n\nStopping early...")
    finally:
        # Display summary
        print("\n" + "=" * 50)
        print("📋 Data Summary (Last 30 seconds)")
        print("=" * 50)
        
        all_readings = client.get_all_readings()
        for sensor_id, data in all_readings.items():
            print(f"\n{sensor_id}:")
            for key, value in data.items():
                if key != "timestamp":
                    print(f"  {key}: {value}")
        
        await client.disconnect()


async def irrigation_decision_mode():
    """Example 4: Real-world usage - making irrigation decisions."""
    print("=" * 50)
    print("Example 4: Irrigation Decision Mode")
    print("=" * 50)
    
    client = SensorStreamClient()
    
    # Authenticate
    if not client.login("test_user", "test_pass"):
        return
    
    # Connect to stream
    if not await client.connect():
        return
    
    # Define irrigation logic
    irrigation_rules = {
        "V1": {"min_moisture": 30, "max_moisture": 70},
        "V2": {"min_moisture": 30, "max_moisture": 70},
        "V3": {"min_moisture": 30, "max_moisture": 70},
        "V4": {"min_moisture": 30, "max_moisture": 70},
        "V5": {"min_moisture": 40, "max_moisture": 80},  # Potatoes need more moisture
    }
    
    async def check_irrigation(message):
        """Check if irrigation is needed based on moisture."""
        if message["type"] == "sensor_reading":
            data = message["data"]
            sensor_id = data["sensor_id"]
            moisture = data.get("moisture")
            
            if moisture is not None and sensor_id in irrigation_rules:
                rules = irrigation_rules[sensor_id]
                
                if moisture < rules["min_moisture"]:
                    print(f"   💧 START IRRIGATION: {sensor_id} moisture={moisture}%")
                    # TODO: Call irrigation API to start irrigation
                elif moisture > rules["max_moisture"]:
                    print(f"   🛑 STOP IRRIGATION: {sensor_id} moisture={moisture}%")
                    # TODO: Call irrigation API to stop irrigation
    
    print("\nMonitoring soil moisture for irrigation decisions...\n")
    
    try:
        await client.receive_updates(callback=check_irrigation)
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        await client.disconnect()


def main():
    """Main entry point."""
    print("\n🌱 Smart Irrigation - WebSocket Sensor Stream Client\n")
    
    print("Select example to run:")
    print("1. Continuous Loop (default)")
    print("2. Custom Callback")
    print("3. Batch Processing")
    print("4. Irrigation Decision Logic")
    print("0. Exit")
    
    choice = input("\nEnter choice (0-4): ").strip() or "1"
    
    examples = {
        "1": main_loop_mode,
        "2": custom_callback_mode,
        "3": batch_mode,
        "4": irrigation_decision_mode,
    }
    
    if choice in examples:
        asyncio.run(examples[choice]())
    else:
        print("Exiting...")


if __name__ == "__main__":
    main()
