# InfluxDB Setup Guide

## Overview
This guide explains how to set up InfluxDB 2.x for the Smart Irrigation API, including installation, configuration, and data schema setup.

---

## Prerequisites
- InfluxDB 2.x (version 2.0 or higher)
- Docker (optional, for containerized setup)
- Admin access to InfluxDB instance

---

## Installation Options

### Option 1: Docker Installation (Recommended)

1. **Pull InfluxDB Docker Image**
```bash
docker pull influxdb:2.7
```

2. **Run InfluxDB Container**
```bash
docker run -d \
  --name influxdb \
  -p 8086:8086 \
  -v influxdb-data:/var/lib/influxdb2 \
  -v influxdb-config:/etc/influxdb2 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword123 \
  -e DOCKER_INFLUXDB_INIT_ORG=smart-irrigation \
  -e DOCKER_INFLUXDB_INIT_BUCKET=sensors \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=your-super-secret-token \
  influxdb:2.7
```

3. **Verify Installation**
```bash
docker ps | grep influxdb
curl http://localhost:8086/health
```

### Option 2: Direct Installation

#### Ubuntu/Debian
```bash
# Add InfluxDB repository
wget -q https://repos.influxdata.com/influxdata-archive_compat.key
echo '23a1c8836f0afc5ed24e0486339d7cc8f6790b83886c4c96995b88a061c5bb5d influxdata-archive_compat.key' | sha256sum -c && cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null

echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list

# Install InfluxDB
sudo apt-get update
sudo apt-get install influxdb2

# Start service
sudo systemctl start influxdb
sudo systemctl enable influxdb
```

#### macOS
```bash
# Using Homebrew
brew install influxdb

# Start service
brew services start influxdb
```

#### Windows
Download installer from: https://portal.influxdata.com/downloads/

---

## Initial Setup

### 1. Access InfluxDB UI
Navigate to: http://localhost:8086

### 2. Complete Setup Wizard
1. Click "Get Started"
2. Create initial user:
   - Username: `admin`
   - Password: (choose secure password)
   - Organization: `smart-irrigation`
   - Bucket: `sensors`
3. Save the generated token securely

### 3. Generate API Token

If you need to create a new token:

1. Go to **Data** → **Tokens** → **Generate Token**
2. Select "All Access Token" or create a custom token with:
   - Read/Write access to `sensors` bucket
3. Copy the token value
4. Add to your `.env` file:
```env
INFLUXDB_TOKEN=your-token-here
```

---

## Data Schema

### Measurement Structure

The API expects sensor data to follow this structure:

#### Tags (Indexed)
- `sensor_id`: Unique identifier for the sensor (required)
- `sensor_name`: Human-readable name (optional)
- `sensor_type`: Type of sensor (optional but recommended)
- `location`: Physical location (optional)

#### Fields
- `value`: Numeric sensor reading (required)

#### Measurements (Recommended Names)
- `temperature`: Temperature readings
- `humidity`: Humidity readings
- `soil_moisture`: Soil moisture readings
- `pressure`: Atmospheric pressure
- `light`: Light intensity
- `rainfall`: Rainfall measurements
- `wind_speed`: Wind speed

### Example Data Point

**Line Protocol Format:**
```
temperature,sensor_id=sensor_temp_001,sensor_name=Temp\ Sensor\ 1,sensor_type=temperature,location=Field\ A value=25.5 1700000000000000000
```

**Broken Down:**
- **Measurement**: `temperature`
- **Tags**: 
  - `sensor_id=sensor_temp_001`
  - `sensor_name=Temp Sensor 1`
  - `sensor_type=temperature`
  - `location=Field A`
- **Field**: `value=25.5`
- **Timestamp**: `1700000000000000000` (nanoseconds since epoch)

---

## Writing Sample Data

### Using InfluxDB UI

1. Go to **Data** → **Buckets** → **sensors** → **Add Data** → **Line Protocol**
2. Paste sample data:

```
temperature,sensor_id=sensor_temp_001,sensor_name=Temperature\ Sensor\ 1,sensor_type=temperature,location=Field\ A\ -\ Zone\ 1 value=25.5
temperature,sensor_id=sensor_temp_001,sensor_name=Temperature\ Sensor\ 1,sensor_type=temperature,location=Field\ A\ -\ Zone\ 1 value=24.8
temperature,sensor_id=sensor_temp_001,sensor_name=Temperature\ Sensor\ 1,sensor_type=temperature,location=Field\ A\ -\ Zone\ 1 value=26.2

humidity,sensor_id=sensor_humidity_001,sensor_name=Humidity\ Sensor\ 1,sensor_type=humidity,location=Field\ A\ -\ Zone\ 1 value=65.2
humidity,sensor_id=sensor_humidity_001,sensor_name=Humidity\ Sensor\ 1,sensor_type=humidity,location=Field\ A\ -\ Zone\ 1 value=63.8
humidity,sensor_id=sensor_humidity_001,sensor_name=Humidity\ Sensor\ 1,sensor_type=humidity,location=Field\ A\ -\ Zone\ 1 value=67.5

soil_moisture,sensor_id=sensor_soil_001,sensor_name=Soil\ Moisture\ Sensor\ 1,sensor_type=soil_moisture,location=Field\ A\ -\ Zone\ 1 value=45.0
soil_moisture,sensor_id=sensor_soil_001,sensor_name=Soil\ Moisture\ Sensor\ 1,sensor_type=soil_moisture,location=Field\ A\ -\ Zone\ 1 value=42.3
soil_moisture,sensor_id=sensor_soil_001,sensor_name=Soil\ Moisture\ Sensor\ 1,sensor_type=soil_moisture,location=Field\ A\ -\ Zone\ 1 value=48.7
```

3. Click **Write Data**

### Using Python

```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

# Connection settings
url = "http://localhost:8086"
token = "your-token-here"
org = "smart-irrigation"
bucket = "sensors"

# Create client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Write sample data
points = [
    Point("temperature")
        .tag("sensor_id", "sensor_temp_001")
        .tag("sensor_name", "Temperature Sensor 1")
        .tag("sensor_type", "temperature")
        .tag("location", "Field A - Zone 1")
        .field("value", 25.5)
        .time(datetime.utcnow()),
    
    Point("humidity")
        .tag("sensor_id", "sensor_humidity_001")
        .tag("sensor_name", "Humidity Sensor 1")
        .tag("sensor_type", "humidity")
        .tag("location", "Field A - Zone 1")
        .field("value", 65.2)
        .time(datetime.utcnow()),
    
    Point("soil_moisture")
        .tag("sensor_id", "sensor_soil_001")
        .tag("sensor_name", "Soil Moisture Sensor 1")
        .tag("sensor_type", "soil_moisture")
        .tag("location", "Field A - Zone 1")
        .field("value", 45.0)
        .time(datetime.utcnow()),
]

write_api.write(bucket=bucket, org=org, record=points)
print("Sample data written successfully!")

client.close()
```

### Using CLI

```bash
# Install InfluxDB CLI
brew install influxdb-cli  # macOS
# or download from https://portal.influxdata.com/downloads/

# Configure CLI
influx config create \
  --config-name smart-irrigation \
  --host-url http://localhost:8086 \
  --org smart-irrigation \
  --token your-token-here \
  --active

# Write data
influx write \
  --bucket sensors \
  --precision s \
  'temperature,sensor_id=sensor_temp_001,sensor_type=temperature value=25.5'
```

---

## Querying Data

### Using Flux Query Language

#### Get Latest Reading
```flux
from(bucket: "sensors")
  |> range(start: -7d)
  |> filter(fn: (r) => r["sensor_id"] == "sensor_temp_001")
  |> last()
```

#### Get Historical Data
```flux
from(bucket: "sensors")
  |> range(start: -24h)
  |> filter(fn: (r) => r["sensor_id"] == "sensor_temp_001")
  |> sort(columns: ["_time"], desc: false)
```

#### Calculate Statistics
```flux
from(bucket: "sensors")
  |> range(start: -24h)
  |> filter(fn: (r) => r["sensor_id"] == "sensor_temp_001")
  |> group()
  |> aggregateWindow(every: 1h, fn: mean)
```

### Using Data Explorer (UI)

1. Go to **Data Explorer**
2. Select bucket: `sensors`
3. Build query visually or use Script Editor for Flux
4. Click **Submit** to view results

---

## Configuration for API

### 1. Create `.env` File

In your project root:
```env
# InfluxDB Configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token-from-influxdb-ui
INFLUXDB_ORG=smart-irrigation
INFLUXDB_BUCKET=sensors

# Cache Configuration
CACHE_TTL_SECONDS=300
```

### 2. Verify Connection

```python
from influxdb_client import InfluxDBClient

client = InfluxDBClient(
    url="http://localhost:8086",
    token="your-token-here",
    org="smart-irrigation"
)

# Test connection
health = client.health()
print(f"InfluxDB Status: {health.status}")
print(f"Message: {health.message}")

client.close()
```

---

## Backup and Restore

### Backup InfluxDB Data

```bash
# Using Docker
docker exec influxdb influx backup /backup -t your-token-here

# Copy backup from container
docker cp influxdb:/backup ./influxdb-backup

# Or using influx CLI
influx backup /path/to/backup -t your-token-here
```

### Restore InfluxDB Data

```bash
# Using Docker
docker cp ./influxdb-backup influxdb:/backup
docker exec influxdb influx restore /backup -t your-token-here

# Or using influx CLI
influx restore /path/to/backup -t your-token-here
```

---

## Performance Optimization

### 1. Retention Policies

Set up automatic data deletion for old data:

```bash
influx bucket update \
  --name sensors \
  --retention 30d
```

Or via UI: **Data** → **Buckets** → **sensors** → **Edit** → Set retention period

### 2. Downsampling (Advanced)

Create tasks to downsample high-frequency data:

```flux
option task = {name: "downsample-hourly", every: 1h}

from(bucket: "sensors")
  |> range(start: -1h)
  |> aggregateWindow(every: 5m, fn: mean)
  |> to(bucket: "sensors-downsampled")
```

### 3. Index Optimization

Keep tags selective:
- Use tags for frequently filtered fields (sensor_id, sensor_type, location)
- Use fields for numeric values and measurements
- Avoid high-cardinality tags (unique values > 100k)

---

## Monitoring

### Check InfluxDB Status

```bash
# Using CLI
influx ping

# Using HTTP
curl http://localhost:8086/health
```

### View Metrics

Access InfluxDB UI: http://localhost:8086
- **Usage**: View data usage and query performance
- **System**: Monitor CPU, memory, and disk usage
- **Alerts**: Set up alerts for system issues

---

## Security Best Practices

### 1. Token Management
- Use separate tokens for read-only and write operations
- Rotate tokens regularly
- Never commit tokens to version control

### 2. Network Security
- Use HTTPS in production
- Restrict access with firewall rules
- Use VPN for remote access

### 3. Authentication
- Use strong passwords
- Enable 2FA for admin accounts (if available)
- Limit token permissions to minimum required

### 4. Docker Security
```bash
# Run with limited privileges
docker run -d \
  --name influxdb \
  -p 8086:8086 \
  --user 1000:1000 \
  -v influxdb-data:/var/lib/influxdb2 \
  influxdb:2.7
```

---

## Troubleshooting

### Connection Issues

**Problem**: `Connection refused`
```
Solution:
1. Check if InfluxDB is running: docker ps | grep influxdb
2. Verify port 8086 is not blocked
3. Check firewall rules
```

**Problem**: `Unauthorized` or `Invalid token`
```
Solution:
1. Verify token is correct in .env file
2. Check token has required permissions
3. Regenerate token if needed
```

### Query Issues

**Problem**: No data returned
```
Solution:
1. Verify bucket name is correct
2. Check time range (use wider range for testing)
3. Verify sensor_id matches exactly (case-sensitive)
4. Use Data Explorer to test queries manually
```

**Problem**: Query timeout
```
Solution:
1. Reduce time range
2. Add more specific filters
3. Increase query timeout in client settings
4. Check InfluxDB resource usage
```

---

## Additional Resources

- [InfluxDB Documentation](https://docs.influxdata.com/influxdb/v2.7/)
- [Flux Query Language](https://docs.influxdata.com/flux/v0.x/)
- [Python Client Library](https://github.com/influxdata/influxdb-client-python)
- [InfluxDB University](https://university.influxdata.com/)

---

## Support

For InfluxDB-specific issues:
1. Check [InfluxDB Community Forums](https://community.influxdata.com/)
2. Review [GitHub Issues](https://github.com/influxdata/influxdb/issues)
3. Contact InfluxData support (Enterprise customers)

For API integration issues:
- Contact Rayyan
- Review main project documentation
