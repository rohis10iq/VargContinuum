"""
WebSocket Test Script for Smart Irrigation API
This script demonstrates how to connect to and test the WebSocket endpoints.
"""

import asyncio
import json
import websockets
from datetime import datetime


async def test_specific_sensor_stream():
    """Test connection to specific sensor stream endpoint."""
    uri = "ws://localhost:8000/ws/sensors/soil_sensor_01"
    
    print(f"\n{'='*60}")
    print(f"Testing: Specific Sensor Stream (/ws/sensors/soil_sensor_01)")
    print(f"{'='*60}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Receive initial messages (connection confirmation + latest data)
            for i in range(3):  # Receive first few messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"\n📩 Received message {i+1}:")
                    print(json.dumps(data, indent=2, default=str))
                except asyncio.TimeoutError:
                    print(f"  (No more messages within timeout)")
                    break
            
            print(f"\n✅ Specific sensor stream test completed")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_all_sensors_stream():
    """Test connection to all sensors stream endpoint."""
    uri = "ws://localhost:8000/ws/sensors/stream"
    
    print(f"\n{'='*60}")
    print(f"Testing: All Sensors Stream (/ws/sensors/stream)")
    print(f"{'='*60}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Receive initial messages
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"\n📩 Received message {i+1}:")
                    print(json.dumps(data, indent=2, default=str))
                except asyncio.TimeoutError:
                    print(f"  (No more messages within timeout)")
                    break
            
            print(f"\n✅ All sensors stream test completed")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_multiple_connections():
    """Test multiple concurrent connections."""
    print(f"\n{'='*60}")
    print(f"Testing: Multiple Concurrent Connections")
    print(f"{'='*60}")
    
    async def listen_to_stream(client_id, uri):
        """Simulate a client listening to a stream."""
        try:
            async with websockets.connect(uri) as websocket:
                print(f"  Client {client_id}: Connected")
                
                # Listen for a few messages
                for i in range(2):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        data = json.loads(message)
                        print(f"  Client {client_id}: Received {data.get('type', 'unknown')} message")
                    except asyncio.TimeoutError:
                        break
                
                print(f"  Client {client_id}: Disconnecting")
        except Exception as e:
            print(f"  Client {client_id}: Error - {e}")
    
    # Create 3 concurrent connections
    tasks = [
        listen_to_stream(1, "ws://localhost:8000/ws/sensors/stream"),
        listen_to_stream(2, "ws://localhost:8000/ws/sensors/stream"),
        listen_to_stream(3, "ws://localhost:8000/ws/sensors/soil_sensor_01"),
    ]
    
    await asyncio.gather(*tasks)
    print(f"\n✅ Multiple connections test completed")


async def test_heartbeat():
    """Test heartbeat mechanism by listening for ping messages."""
    uri = "ws://localhost:8000/ws/sensors/stream"
    
    print(f"\n{'='*60}")
    print(f"Testing: Heartbeat Mechanism (this will take ~35 seconds)")
    print(f"{'='*60}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected, waiting for heartbeat...")
            print(f"   (Heartbeat interval is 30 seconds)")
            
            start_time = datetime.now()
            heartbeat_received = False
            
            # Listen for up to 40 seconds to catch a heartbeat
            while (datetime.now() - start_time).total_seconds() < 40:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'heartbeat':
                        elapsed = (datetime.now() - start_time).total_seconds()
                        print(f"\n💓 Heartbeat received after {elapsed:.1f} seconds!")
                        print(f"   Message: {json.dumps(data, indent=2, default=str)}")
                        heartbeat_received = True
                        break
                    else:
                        print(f"   Received {data.get('type', 'unknown')} message (not heartbeat yet)")
                        
                except asyncio.TimeoutError:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"   Still waiting... ({elapsed:.0f}s elapsed)")
            
            if heartbeat_received:
                print(f"\n✅ Heartbeat test completed successfully")
            else:
                print(f"\n⚠️ No heartbeat received within 40 seconds")
                
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all tests."""
    print(f"\n{'#'*60}")
    print(f"# WebSocket Infrastructure Test Suite")
    print(f"# Smart Irrigation API")
    print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    print(f"\nℹ️  Note: Make sure the API server is running on http://localhost:8000")
    print(f"ℹ️  Start server with: python main.py")
    
    input("\nPress Enter to start tests...")
    
    # Run tests sequentially
    await test_all_sensors_stream()
    await asyncio.sleep(1)
    
    await test_specific_sensor_stream()
    await asyncio.sleep(1)
    
    await test_multiple_connections()
    await asyncio.sleep(1)
    
    # Ask user if they want to run the long heartbeat test
    print(f"\n{'='*60}")
    response = input("Run heartbeat test? (takes ~35 seconds) [y/N]: ")
    if response.lower() == 'y':
        await test_heartbeat()
    else:
        print("⏭️  Skipping heartbeat test")
    
    print(f"\n{'#'*60}")
    print(f"# All tests completed!")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
