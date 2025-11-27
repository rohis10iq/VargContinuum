"""InfluxDB client utility for querying sensor data."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from config import settings


class InfluxDBManager:
    """Manager class for InfluxDB operations."""
    
    def __init__(self):
        """Initialize InfluxDB client."""
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG
        )
        self.query_api: QueryApi = self.client.query_api()
        self.bucket = settings.INFLUXDB_BUCKET
        self.org = settings.INFLUXDB_ORG
    
    def close(self):
        """Close the InfluxDB client connection."""
        self.client.close()
    
    def get_all_sensors(self) -> List[Dict[str, Any]]:
        """
        Get list of all sensors with their metadata.
        
        Returns:
            List of sensor dictionaries with id, name, type, location, unit, status
        """
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -30d)
            |> group(columns: ["sensor_id"])
            |> distinct(column: "sensor_id")
            |> limit(n: 1000)
        '''
        
        try:
            tables = self.query_api.query(query, org=self.org)
            sensors = []
            seen_sensors = set()
            
            for table in tables:
                for record in table.records:
                    sensor_id = record.values.get("sensor_id")
                    if sensor_id and sensor_id not in seen_sensors:
                        seen_sensors.add(sensor_id)
                        
                        # Extract sensor metadata from tags
                        sensor_type = record.values.get("sensor_type", "unknown")
                        location = record.values.get("location", None)
                        unit = record.values.get("_measurement", "")
                        
                        sensors.append({
                            "id": sensor_id,
                            "name": record.values.get("sensor_name", sensor_id),
                            "type": sensor_type,
                            "location": location,
                            "unit": self._get_unit_for_measurement(unit),
                            "status": "active"
                        })
            
            return sensors
        except Exception as e:
            print(f"Error querying all sensors: {e}")
            return []
    
    def get_sensor_details(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific sensor.
        
        Args:
            sensor_id: The sensor identifier
            
        Returns:
            Dictionary with sensor details or None if not found
        """
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -7d)
            |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
            |> last()
        '''
        
        try:
            tables = self.query_api.query(query, org=self.org)
            
            for table in tables:
                for record in table.records:
                    return {
                        "id": sensor_id,
                        "name": record.values.get("sensor_name", sensor_id),
                        "type": record.values.get("sensor_type", "unknown"),
                        "location": record.values.get("location", None),
                        "unit": self._get_unit_for_measurement(record.get_measurement()),
                        "status": "active"
                    }
            
            return None
        except Exception as e:
            print(f"Error querying sensor details: {e}")
            return None
    
    def get_latest_reading(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest reading for a sensor.
        
        Args:
            sensor_id: The sensor identifier
            
        Returns:
            Dictionary with timestamp, value, unit or None if not found
        """
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -7d)
            |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
            |> last()
        '''
        
        try:
            tables = self.query_api.query(query, org=self.org)
            
            for table in tables:
                for record in table.records:
                    return {
                        "timestamp": record.get_time(),
                        "value": record.get_value(),
                        "unit": self._get_unit_for_measurement(record.get_measurement())
                    }
            
            return None
        except Exception as e:
            print(f"Error querying latest reading: {e}")
            return None
    
    def get_sensor_history(
        self,
        sensor_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
        interval: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical readings for a sensor.
        
        Args:
            sensor_id: The sensor identifier
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            limit: Maximum number of readings to return
            interval: Aggregation interval (e.g., '1h', '15m', '30s') for downsampling
            
        Returns:
            List of reading dictionaries with timestamp, value, unit
        """
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.utcnow()
        
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Build query with optional aggregation
        if interval:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start_str}, stop: {end_str})
                |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
                |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
                |> sort(columns: ["_time"], desc: false)
                |> limit(n: {limit})
            '''
        else:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start_str}, stop: {end_str})
                |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
                |> sort(columns: ["_time"], desc: false)
                |> limit(n: {limit})
            '''
        
        try:
            tables = self.query_api.query(query, org=self.org)
            readings = []
            
            for table in tables:
                unit = self._get_unit_for_measurement(table.records[0].get_measurement()) if table.records else ""
                for record in table.records:
                    readings.append({
                        "timestamp": record.get_time(),
                        "value": record.get_value(),
                        "unit": unit
                    })
            
            return readings
        except Exception as e:
            print(f"Error querying sensor history: {e}")
            return []
    
    def get_sensor_statistics(
        self,
        sensor_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get statistical summary for a sensor.
        
        Args:
            sensor_id: The sensor identifier
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            
        Returns:
            Dictionary with min, max, avg values or None if no data
        """
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.utcnow()
        
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_str}, stop: {end_str})
            |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
            |> group()
            |> reduce(fn: (r, accumulator) => ({{
                min: if r._value < accumulator.min then r._value else accumulator.min,
                max: if r._value > accumulator.max then r._value else accumulator.max,
                sum: accumulator.sum + r._value,
                count: accumulator.count + 1.0
            }}), identity: {{min: 999999.0, max: -999999.0, sum: 0.0, count: 0.0}})
            |> map(fn: (r) => ({{ r with avg: r.sum / r.count }}))
        '''
        
        try:
            tables = self.query_api.query(query, org=self.org)
            
            for table in tables:
                for record in table.records:
                    return {
                        "min": record.values.get("min"),
                        "max": record.values.get("max"),
                        "avg": record.values.get("avg")
                    }
            
            return None
        except Exception as e:
            print(f"Error querying sensor statistics: {e}")
            return None
    
    def _get_unit_for_measurement(self, measurement: str) -> str:
        """
        Map measurement names to units.
        
        Args:
            measurement: The measurement name
            
        Returns:
            The unit string
        """
        unit_mapping = {
            "temperature": "°C",
            "humidity": "%",
            "soil_moisture": "%",
            "pressure": "hPa",
            "light": "lux",
            "rainfall": "mm",
            "wind_speed": "m/s"
        }
        return unit_mapping.get(measurement.lower(), "")


# Global instance
influxdb_manager = InfluxDBManager()


def get_influxdb_manager() -> InfluxDBManager:
    """Get the global InfluxDB manager instance."""
    return influxdb_manager
