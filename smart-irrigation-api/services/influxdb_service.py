"""InfluxDB service for time-series sensor data storage and querying."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from influxdb_client import InfluxDBClient, Point, QueryApi, WriteApi, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from config import settings


class InfluxDBService:
    """Service for managing sensor data in InfluxDB."""
    
    def __init__(self):
        """Initialize InfluxDB client."""
        self.client: Optional[InfluxDBClient] = None
        self.write_api: Optional[WriteApi] = None
        self.query_api: Optional[QueryApi] = None
        
    def connect(self):
        """Connect to InfluxDB."""
        if not settings.INFLUXDB_TOKEN:
            raise ValueError("InfluxDB token not configured. Please set INFLUXDB_TOKEN in .env file.")
        
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        
    def close(self):
        """Close InfluxDB connection."""
        if self.client:
            self.client.close()
            
    def write_sensor_data(
        self, 
        sensor_id: str, 
        sensor_type: str, 
        value: float,
        location: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Write a sensor reading to InfluxDB.
        
        Args:
            sensor_id: Unique sensor identifier
            sensor_type: Type of sensor (e.g., soil_moisture, temperature)
            value: Sensor reading value
            location: Physical location of sensor
            timestamp: Reading timestamp (defaults to now)
            
        Returns:
            True if write successful
        """
        try:
            point = Point("sensor_reading") \
                .tag("sensor_id", sensor_id) \
                .tag("sensor_type", sensor_type)
            
            if location:
                point = point.tag("location", location)
                
            point = point.field("value", float(value))
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(
                bucket=settings.INFLUXDB_BUCKET,
                org=settings.INFLUXDB_ORG,
                record=point
            )
            return True
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")
            return False
    
    def query_24h_history(
        self, 
        sensor_id: Optional[str] = None,
        sensor_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query 24-hour sensor history with 5-minute aggregation.
        
        Args:
            sensor_id: Filter by sensor ID
            sensor_type: Filter by sensor type
            
        Returns:
            List of data points with timestamps and values
        """
        filters = self._build_filters(sensor_id, sensor_type)
        
        query = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: -24h)
          |> filter(fn: (r) => r["_measurement"] == "sensor_reading")
          {filters}
          |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
          |> yield(name: "mean")
        '''
        
        return self._execute_query(query)
    
    def query_7d_history(
        self, 
        sensor_id: Optional[str] = None,
        sensor_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query 7-day sensor history with 1-hour aggregation.
        
        Args:
            sensor_id: Filter by sensor ID
            sensor_type: Filter by sensor type
            
        Returns:
            List of data points with timestamps and values
        """
        filters = self._build_filters(sensor_id, sensor_type)
        
        query = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: -7d)
          |> filter(fn: (r) => r["_measurement"] == "sensor_reading")
          {filters}
          |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
          |> yield(name: "mean")
        '''
        
        return self._execute_query(query)
    
    def query_30d_history(
        self, 
        sensor_id: Optional[str] = None,
        sensor_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query 30-day sensor history with 6-hour aggregation.
        
        Args:
            sensor_id: Filter by sensor ID
            sensor_type: Filter by sensor type
            
        Returns:
            List of data points with timestamps and values
        """
        filters = self._build_filters(sensor_id, sensor_type)
        
        query = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: -30d)
          |> filter(fn: (r) => r["_measurement"] == "sensor_reading")
          {filters}
          |> aggregateWindow(every: 6h, fn: mean, createEmpty: false)
          |> yield(name: "mean")
        '''
        
        return self._execute_query(query)
    
    def query_custom_aggregation(
        self,
        start_time: datetime,
        stop_time: Optional[datetime] = None,
        aggregation_window: str = "5m",
        aggregation_function: str = "mean",
        sensor_id: Optional[str] = None,
        sensor_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query sensor data with custom time range and aggregation.
        
        Args:
            start_time: Query start time
            stop_time: Query stop time (defaults to now)
            aggregation_window: Window size (e.g., 5m, 1h, 1d)
            aggregation_function: Aggregation function (mean, max, min, sum, count)
            sensor_id: Filter by sensor ID
            sensor_type: Filter by sensor type
            
        Returns:
            List of data points with timestamps and values
        """
        filters = self._build_filters(sensor_id, sensor_type)
        
        # Format timestamps for Flux
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        stop_str = stop_time.strftime("%Y-%m-%dT%H:%M:%SZ") if stop_time else "now()"
        
        query = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: {start_str}, stop: {stop_str})
          |> filter(fn: (r) => r["_measurement"] == "sensor_reading")
          {filters}
          |> aggregateWindow(every: {aggregation_window}, fn: {aggregation_function}, createEmpty: false)
          |> yield(name: "{aggregation_function}")
        '''
        
        return self._execute_query(query)
    
    def _build_filters(
        self, 
        sensor_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        location: Optional[str] = None
    ) -> str:
        """Build Flux filter clauses."""
        filters = []
        
        if sensor_id:
            filters.append(f'|> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")')
        if sensor_type:
            filters.append(f'|> filter(fn: (r) => r["sensor_type"] == "{sensor_type}")')
        if location:
            filters.append(f'|> filter(fn: (r) => r["location"] == "{location}")')
            
        return "\n          ".join(filters)
    
    def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a Flux query and return results.
        
        Args:
            query: Flux query string
            
        Returns:
            List of dictionaries containing query results
        """
        try:
            tables = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            results = []
            
            for table in tables:
                for record in table.records:
                    results.append({
                        "timestamp": record.get_time(),
                        "value": record.get_value(),
                        "sensor_id": record.values.get("sensor_id"),
                        "sensor_type": record.values.get("sensor_type"),
                        "location": record.values.get("location")
                    })
            
            return results
        except Exception as e:
            print(f"Error executing query: {e}")
            return []
    
    def get_all_sensors(self) -> List[Dict[str, Any]]:
        """
        Get list of all unique sensors.
        
        Returns:
            List of sensors with their IDs, types, and locations
        """
        query = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: -30d)
          |> filter(fn: (r) => r["_measurement"] == "sensor_reading")
          |> keep(columns: ["sensor_id", "sensor_type", "location"])
          |> distinct(column: "sensor_id")
        '''
        
        try:
            tables = self.query_api.query(query, org=settings.INFLUXDB_ORG)
            sensors = []
            seen_ids = set()
            
            for table in tables:
                for record in table.records:
                    sensor_id = record.values.get("sensor_id")
                    if sensor_id and sensor_id not in seen_ids:
                        sensors.append({
                            "sensor_id": sensor_id,
                            "sensor_type": record.values.get("sensor_type"),
                            "location": record.values.get("location")
                        })
                        seen_ids.add(sensor_id)
            
            return sensors
        except Exception as e:
            print(f"Error getting all sensors: {e}")
            return []
    
    def get_sensor_latest(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent reading for a specific sensor.
        
        Args:
            sensor_id: Sensor identifier
            
        Returns:
            Latest sensor reading or None
        """
        query = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: -7d)
          |> filter(fn: (r) => r["_measurement"] == "sensor_reading")
          |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
          |> last()
        '''
        
        results = self._execute_query(query)
        return results[0] if results else None
    
    def get_dashboard_summary(self) -> List[Dict[str, Any]]:
        """
        Get latest reading for all sensors (dashboard summary).
        
        Returns:
            List of latest readings for each sensor
        """
        query = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: -24h)
          |> filter(fn: (r) => r["_measurement"] == "sensor_reading")
          |> group(columns: ["sensor_id"])
          |> last()
        '''
        
        return self._execute_query(query)


# Global instance
influxdb_service = InfluxDBService()
