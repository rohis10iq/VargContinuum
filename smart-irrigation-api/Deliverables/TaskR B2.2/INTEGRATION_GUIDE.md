# WebSocket Integration Guide

## Quick Start

### 1. Start the API Server
```bash
cd /home/rayyan/Desktop/VargContinuum/smart-irrigation-api
python -m uvicorn main:app --reload --port 8000
```

### 2. Start MQTT Broker (Optional but Recommended)
```bash
mosquitto -c /etc/mosquitto/mosquitto.conf
# OR with Docker:
docker run -d -p 1883:1883 eclipse-mosquitto
```

### 3. Get JWT Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test_pass"
  }'
```

**First time? Register first:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test_pass",
    "role": "user"
  }'
```

### 4. Test WebSocket Connection
```python
import asyncio
import json
import websockets

async def test_websocket():
    token = "YOUR_JWT_TOKEN_HERE"
    async with websockets.connect(f"ws://localhost:8000/ws/sensors?token={token}") as ws:
        # Receive connection status
        msg = await ws.recv()
        print(f"Connected: {json.loads(msg)}")
        
        # Listen for sensor updates
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data["type"] == "sensor_reading":
                print(f"Update: {data['data']}")

asyncio.run(test_websocket())
```

## Frontend Framework Integration

### React Dashboard Component
```javascript
import React, { useEffect, useState } from 'react';

const SensorDashboard = ({ token }) => {
  const [sensors, setSensors] = useState({});
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(
      `ws://localhost:8000/ws/sensors?token=${token}`
    );

    ws.onopen = () => {
      console.log('Connected to sensor stream');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'sensor_reading') {
        const { sensor_id, moisture, temperature, humidity } = message.data;
        
        setSensors(prev => ({
          ...prev,
          [sensor_id]: {
            moisture,
            temperature,
            humidity,
            timestamp: message.timestamp
          }
        }));
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      setConnected(false);
      // Attempt to reconnect in 5 seconds
      setTimeout(() => window.location.reload(), 5000);
    };

    return () => ws.close();
  }, [token]);

  return (
    <div>
      <h2>Sensor Dashboard {connected ? '🟢' : '🔴'}</h2>
      <div className="sensor-grid">
        {Object.entries(sensors).map(([id, data]) => (
          <div key={id} className="sensor-card">
            <h3>{id}</h3>
            <p>Moisture: {data.moisture}%</p>
            <p>Temperature: {data.temperature}°C</p>
            <p>Humidity: {data.humidity}%</p>
            <small>{new Date(data.timestamp).toLocaleTimeString()}</small>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SensorDashboard;
```

### Vue.js Component
```vue
<template>
  <div class="dashboard">
    <h2>Live Sensors <span :class="connected ? 'connected' : 'disconnected'">●</span></h2>
    
    <div class="sensor-grid">
      <div v-for="(data, sensorId) in sensors" :key="sensorId" class="sensor-card">
        <h3>{{ sensorId }}</h3>
        <p>Moisture: {{ data.moisture }}%</p>
        <p>Temperature: {{ data.temperature }}°C</p>
        <p>Humidity: {{ data.humidity }}%</p>
        <small>{{ formatTime(data.timestamp) }}</small>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['token'],
  data() {
    return {
      sensors: {},
      connected: false,
      ws: null
    };
  },
  mounted() {
    this.connect();
  },
  methods: {
    connect() {
      this.ws = new WebSocket(
        `ws://localhost:8000/ws/sensors?token=${this.token}`
      );
      
      this.ws.onopen = () => {
        this.connected = true;
        console.log('WebSocket connected');
      };
      
      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'sensor_reading') {
          const { sensor_id, ...data } = message.data;
          this.$set(this.sensors, sensor_id, {
            ...data,
            timestamp: message.timestamp
          });
        }
      };
      
      this.ws.onclose = () => {
        this.connected = false;
        setTimeout(() => this.connect(), 5000);
      };
    },
    formatTime(isoString) {
      return new Date(isoString).toLocaleTimeString();
    }
  },
  beforeDestroy() {
    if (this.ws) this.ws.close();
  }
};
</script>

<style scoped>
.connected { color: #4caf50; }
.disconnected { color: #f44336; }
</style>
```

### Angular Service
```typescript
import { Injectable } from '@angular/core';
import { Subject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private ws: WebSocket;
  private sensorData$ = new Subject<any>();
  private connectionStatus$ = new Subject<boolean>();

  constructor() {}

  connect(token: string): Observable<any> {
    this.ws = new WebSocket(
      `ws://localhost:8000/ws/sensors?token=${token}`
    );

    this.ws.onopen = () => {
      this.connectionStatus$.next(true);
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'sensor_reading') {
        this.sensorData$.next(message);
      }
    };

    this.ws.onclose = () => {
      this.connectionStatus$.next(false);
    };

    return this.sensorData$.asObservable();
  }

  getConnectionStatus(): Observable<boolean> {
    return this.connectionStatus$.asObservable();
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
```

### Angular Component
```typescript
import { Component, OnInit, OnDestroy } from '@angular/core';
import { WebSocketService } from './websocket.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-sensor-dashboard',
  template: `
    <h2>Live Sensors {{ connected ? '🟢' : '🔴' }}</h2>
    <div class="sensor-grid">
      <div *ngFor="let sensor of sensorData | keyvalue" class="sensor-card">
        <h3>{{ sensor.key }}</h3>
        <p>Moisture: {{ sensor.value.moisture }}%</p>
        <p>Temperature: {{ sensor.value.temperature }}°C</p>
        <p>Humidity: {{ sensor.value.humidity }}%</p>
      </div>
    </div>
  `
})
export class SensorDashboardComponent implements OnInit, OnDestroy {
  sensorData: any = {};
  connected = false;
  private subscriptions: Subscription[] = [];

  constructor(private wsService: WebSocketService) {}

  ngOnInit() {
    const token = localStorage.getItem('auth_token');
    
    this.subscriptions.push(
      this.wsService.connect(token).subscribe((message) => {
        const { sensor_id, ...data } = message.data;
        this.sensorData[sensor_id] = data;
      })
    );

    this.subscriptions.push(
      this.wsService.getConnectionStatus().subscribe(
        status => this.connected = status
      )
    );
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
    this.wsService.disconnect();
  }
}
```

## Message Protocol Reference

### Connection Status Message
```json
{
  "type": "connection_status",
  "data": {
    "status": "connected",
    "client_id": "abc12345",
    "active_clients": 5
  },
  "timestamp": "2025-12-06T14:30:00Z"
}
```

### Sensor Reading Message
```json
{
  "type": "sensor_reading",
  "data": {
    "sensor_id": "V1",
    "moisture": 45.2,
    "temperature": 22.1,
    "humidity": 65.5,
    "light": 800.0
  },
  "timestamp": "2025-12-06T14:30:15Z"
}
```

### Error Message (if applicable)
```json
{
  "type": "error",
  "error": "Authentication failed",
  "code": "AUTH_ERROR",
  "timestamp": "2025-12-06T14:30:30Z"
}
```

## Sensor ID Reference

| Sensor ID | Zone | Purpose |
|-----------|------|---------|
| V1 | Orchard Zone 1 | Moisture, temperature, humidity, light |
| V2 | Orchard Zone 2 | Moisture, temperature, humidity, light |
| V3 | Orchard Zone 3 | Moisture, temperature, humidity, light |
| V4 | Orchard Zone 4 | Moisture, temperature, humidity, light |
| V5 | Potato Field | Moisture, temperature, humidity, light |

## Debugging

### Check WebSocket Connection
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws/sensors?token=YOUR_TOKEN');
ws.onopen = () => console.log('Connected!');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.onerror = (e) => console.error('Error:', e);
```

### Monitor MQTT Traffic
```bash
# Subscribe to all sensor topics
mosquitto_sub -h localhost -t "sensors/#" -v
```

### Check API Logs
```bash
# Terminal running uvicorn will show:
# - Client connections
# - MQTT connection status
# - Broadcast events
# - Errors and warnings
```

## Production Deployment

### Use Environment Variables
```bash
export MQTT_BROKER_URL=mqtt.your-domain.com
export MQTT_BROKER_PORT=8883
export MQTT_USERNAME=your_user
export MQTT_PASSWORD=your_pass
python -m uvicorn main:app --port 8000 --host 0.0.0.0
```

### Enable HTTPS/WSS
```bash
# Reverse proxy with nginx
server {
    listen 443 ssl;
    server_name api.your-domain.com;
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Health Monitoring
```bash
# Add to your monitoring system:
# - WebSocket connection count (active_clients in status message)
# - MQTT broker connectivity
# - Message broadcast rate
# - Error rate
```

## Performance Tips

1. **Reduce Message Frequency:** Increase `WEBSOCKET_RATE_LIMIT_SECONDS`
2. **Batch Updates:** Hold messages in client, update chart every 100ms
3. **Use Chart Libraries:** Recharts, Chart.js handle real-time data well
4. **Implement Backpressure:** Don't render every message on slow clients
5. **Monitor Memory:** WebSocket manager cleans up dead connections automatically

## Support

For issues:
1. Check WebSocket is using correct token
2. Verify MQTT broker is running (if not, check logs for "Connection refused")
3. Ensure client WebSocket library supports `connect()` upgrade
4. Check browser console for client-side errors
5. Verify JWT token hasn't expired (valid for 24 hours by default)
