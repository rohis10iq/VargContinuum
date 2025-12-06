"""InfluxDB connection and query utilities for sensor data."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.query_api import QueryApi
from config import settings
import logging

logger = logging.getLogger(__name__)


class InfluxDBManager:
    """Manager for InfluxDB operations."""
    
    def __init__(self):
        """Initialize InfluxDB client."""
        self.client: Optional[InfluxDBClient] = None
        self.query_api: Optional[QueryApi] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to InfluxDB."""
        try:
            self.client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN,
                org=settings.INFLUXDB_ORG
            )
            self.query_api = self.client.query_api()
            logger.info("Successfully connected to InfluxDB")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            # Continue without raising - will use mock data if InfluxDB unavailable
    
    def close(self):
        """Close InfluxDB connection."""
        if self.client:
            self.client.close()
    
    def query_latest_reading(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest reading for a specific sensor.
        
        Args:
            sensor_id: Sensor identifier (e.g., 'V1', 'V2')
            
        Returns:
            Dictionary with sensor reading data or None
        """
        if not self.query_api:
            return self._get_mock_reading(sensor_id)
        
        try:
            query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
                |> range(start: -24h)
                |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
                |> filter(fn: (r) => r["_measurement"] == "sensor_data")
                |> last()
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            if result and len(result) > 0 and len(result[0].records) > 0:
                record = result[0].records[0]
                return {
                    "timestamp": record.get_time(),
                    "moisture": record.values.get("moisture"),
                    "temperature": record.values.get("temperature"),
                    "humidity": record.values.get("humidity"),
                    "light": record.values.get("light")
                }
        except Exception as e:
            logger.error(f"Error querying latest reading for {sensor_id}: {e}")
        
        return self._get_mock_reading(sensor_id)
    
    def query_sensor_history(
        self,
        sensor_id: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1h"
    ) -> List[Dict[str, Any]]:
        """
        Get historical sensor data with aggregation.
        
        Args:
            sensor_id: Sensor identifier
            start_time: Start of time range
            end_time: End of time range
            interval: Aggregation interval (e.g., '1h', '15m', '1d')
            
        Returns:
            List of sensor readings
        """
        if not self.query_api:
            return self._get_mock_history(sensor_id, start_time, end_time, interval)
        
        try:
            query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
                |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
                |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
                |> filter(fn: (r) => r["_measurement"] == "sensor_data")
                |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            readings = []
            if result and len(result) > 0:
                for record in result[0].records:
                    readings.append({
                        "timestamp": record.get_time(),
                        "moisture": record.values.get("moisture"),
                        "temperature": record.values.get("temperature"),
                        "humidity": record.values.get("humidity"),
                        "light": record.values.get("light")
                    })
            
            return readings if readings else self._get_mock_history(sensor_id, start_time, end_time, interval)
        
        except Exception as e:
            logger.error(f"Error querying history for {sensor_id}: {e}")
            return self._get_mock_history(sensor_id, start_time, end_time, interval)
    
    def query_all_sensors_latest(self) -> Dict[str, Dict[str, Any]]:
        """
        Get latest readings for all sensors.
        
        Returns:
            Dictionary mapping sensor_id to latest reading
        """
        if not self.query_api:
            return self._get_all_mock_readings()
        
        try:
            query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
                |> range(start: -24h)
                |> filter(fn: (r) => r["_measurement"] == "sensor_data")
                |> last()
                |> pivot(rowKey:["_time", "sensor_id"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            
            sensors_data = {}
            if result and len(result) > 0:
                for record in result[0].records:
                    sensor_id = record.values.get("sensor_id")
                    sensors_data[sensor_id] = {
                        "timestamp": record.get_time(),
                        "moisture": record.values.get("moisture"),
                        "temperature": record.values.get("temperature"),
                        "humidity": record.values.get("humidity"),
                        "light": record.values.get("light")
                    }
            
            return sensors_data if sensors_data else self._get_all_mock_readings()
        
        except Exception as e:
            logger.error(f"Error querying all sensors: {e}")
            return self._get_all_mock_readings()
    
    def _get_mock_reading(self, sensor_id: str) -> Dict[str, Any]:
        """Generate mock sensor reading for testing."""
        import random
        return {
            "timestamp": datetime.utcnow(),
            "moisture": round(random.uniform(30.0, 70.0), 1),
            "temperature": round(random.uniform(18.0, 28.0), 1),
            "humidity": round(random.uniform(50.0, 80.0), 1),
            "light": random.randint(200, 800)
        }
    
    def _get_mock_history(
        self,
        sensor_id: str,
        start_time: datetime,
        end_time: datetime,
        interval: str
    ) -> List[Dict[str, Any]]:
        """Generate mock historical data for testing."""
        import random
        
        # Parse interval to determine number of data points
        interval_minutes = self._parse_interval(interval)
        duration_minutes = int((end_time - start_time).total_seconds() / 60)
        num_points = min(duration_minutes // interval_minutes, 100)  # Limit to 100 points
        
        readings = []
        current_time = start_time
        time_delta = timedelta(minutes=interval_minutes)
        
        for _ in range(num_points):
            readings.append({
                "timestamp": current_time,
                "moisture": round(random.uniform(30.0, 70.0), 1),
                "temperature": round(random.uniform(18.0, 28.0), 1),
                "humidity": round(random.uniform(50.0, 80.0), 1),
                "light": random.randint(200, 800)
            })
            current_time += time_delta
        
        return readings
    
    def _get_all_mock_readings(self) -> Dict[str, Dict[str, Any]]:
        """Generate mock readings for all sensors."""
        sensors = ["V1", "V2", "V3", "V4", "V5"]
        return {sensor_id: self._get_mock_reading(sensor_id) for sensor_id in sensors}
    
    @staticmethod
    def _parse_interval(interval: str) -> int:
        """Parse interval string to minutes."""
        if interval.endswith("m"):
            return int(interval[:-1])
        elif interval.endswith("h"):
            return int(interval[:-1]) * 60
        elif interval.endswith("d"):
            return int(interval[:-1]) * 1440
        return 60  # Default to 1 hour


# Global InfluxDB manager instance
influx_manager = InfluxDBManager()


def get_influx_manager() -> InfluxDBManager:
    """Get the global InfluxDB manager instance."""
    return influx_manager
