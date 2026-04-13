"""
GraphHopper Client Utility
Provides functions to interact with GraphHopper routing engine
"""

import requests
import logging
import os
import math
import time
from typing import List, Dict, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GraphHopperClient:
    """
    Client for interacting with GraphHopper API
    Supports both self-hosted and cloud versions
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize GraphHopper client
        
        Args:
            base_url: GraphHopper server URL
            api_key: API key for GraphHopper cloud (optional)
        """
        resolved_api_key = api_key or os.getenv("GRAPHHOPPER_API_KEY")
        resolved_base_url = base_url or os.getenv("GRAPHHOPPER_BASE_URL") or "http://graphhopper:8989"

        self.base_url = resolved_base_url.rstrip('/')
        self.api_key = resolved_api_key
        self.allow_fallback = os.getenv("GRAPHHOPPER_ALLOW_FALLBACK", "true").lower() in {"1", "true", "yes", "y"}
        self.session = requests.Session()
        self.fallback_base_urls = [
            self.base_url,
            "http://host.containers.internal:8989",
            "http://localhost:8989",
        ]

        if self.api_key:
            self.fallback_base_urls.append("https://graphhopper.com/api/1")
        
        if self.api_key:
            self.session.params = {'key': self.api_key}

    @staticmethod
    def _haversine_distance_km(start: Tuple[float, float], end: Tuple[float, float]) -> float:
        """Calculate great-circle distance in kilometers."""
        lat1, lon1 = start
        lat2, lon2 = end

        radius_km = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius_km * c

    @staticmethod
    def _vehicle_speed_kmph(vehicle: str) -> float:
        speed_map = {
            "car": 35.0,
            "bike": 20.0,
            "foot": 5.0,
            "truck": 30.0,
            "motorcycle": 30.0,
        }
        return speed_map.get(vehicle, 30.0)

    def _build_fallback_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        vehicle: str,
        calc_points: bool,
    ) -> Dict:
        distance_km = self._haversine_distance_km(start, end)
        estimated_road_factor = 1.25
        adjusted_distance_km = distance_km * estimated_road_factor
        speed_kmph = self._vehicle_speed_kmph(vehicle)
        time_hours = adjusted_distance_km / max(speed_kmph, 1)
        time_minutes = time_hours * 60

        result = {
            "distance_meters": adjusted_distance_km * 1000,
            "distance_km": adjusted_distance_km,
            "time_ms": time_minutes * 60000,
            "time_minutes": time_minutes,
            "time_hours": time_hours,
            "start_point": start,
            "end_point": end,
            "vehicle": vehicle,
            "estimated": True,
            "calculated_at": datetime.now().isoformat(),
        }

        if calc_points:
            result["points"] = [[start[1], start[0]], [end[1], end[0]]]
            result["instructions"] = [
                {
                    "text": "Estimated straight-line fallback route (GraphHopper unavailable)",
                    "distance": adjusted_distance_km * 1000,
                    "time": time_minutes * 60000,
                }
            ]

        return result

    def _build_fallback_matrix(self, points: List[Tuple[float, float]], vehicle: str) -> Dict:
        speed_kmph = self._vehicle_speed_kmph(vehicle)
        estimated_road_factor = 1.25

        distances = []
        times = []
        for start in points:
            distance_row = []
            time_row = []
            for end in points:
                distance_km = self._haversine_distance_km(start, end) * estimated_road_factor
                time_hours = distance_km / max(speed_kmph, 1)
                distance_row.append(distance_km * 1000)
                time_row.append(time_hours * 3600000)
            distances.append(distance_row)
            times.append(time_row)

        return {
            "distances": distances,
            "times": times,
            "points": points,
            "vehicle": vehicle,
            "estimated": True,
            "calculated_at": datetime.now().isoformat(),
        }
    
    def health_check(self) -> bool:
        """
        Check if GraphHopper service is healthy
        
        Returns:
            bool: True if healthy, False otherwise
        """
        checked_urls = []

        for candidate_url in self.fallback_base_urls:
            if candidate_url in checked_urls:
                continue
            checked_urls.append(candidate_url)

            try:
                response = self.session.get(f"{candidate_url.rstrip('/')}/health", timeout=5)
                if response.status_code == 200:
                    self.base_url = candidate_url.rstrip('/')
                    return True
            except Exception as e:
                logger.warning(f"GraphHopper health check failed for {candidate_url}: {e}")

            if self.api_key:
                try:
                    info_response = self.session.get(f"{candidate_url.rstrip('/')}/info", timeout=5)
                    if info_response.status_code == 200:
                        self.base_url = candidate_url.rstrip('/')
                        return True
                except Exception as e:
                    logger.warning(f"GraphHopper info check failed for {candidate_url}: {e}")

        return False
    
    def get_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        vehicle: str = "car",
        locale: str = "id",
        calc_points: bool = True
    ) -> Dict:
        """
        Calculate route between two points
        
        Args:
            start: (latitude, longitude) tuple for starting point
            end: (latitude, longitude) tuple for destination
            vehicle: Transportation mode (car, bike, foot, etc.)
            locale: Language for instructions (id, en, etc.)
            calc_points: Whether to include detailed route points
        
        Returns:
            dict: Route information including distance, time, and path
            
        Example:
            >>> client = GraphHopperClient()
            >>> route = client.get_route(
            ...     start=(-6.1754, 106.8272),  # Jakarta
            ...     end=(-6.2088, 106.8456),    # South Jakarta
            ...     vehicle="car"
            ... )
            >>> print(f"Distance: {route['distance_km']:.2f} km")
            >>> print(f"Duration: {route['time_minutes']:.1f} minutes")
        """
        url = f"{self.base_url}/route"
        
        params = {
            "point": [f"{start[0]},{start[1]}", f"{end[0]},{end[1]}"],
            "vehicle": vehicle,
            "locale": locale,
            "calc_points": str(calc_points).lower(),
            "points_encoded": "false",
            "instructions": "true"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "paths" not in data or len(data["paths"]) == 0:
                raise ValueError("No route found")
            
            path = data["paths"][0]
            
            result = {
                "distance_meters": path["distance"],
                "distance_km": path["distance"] / 1000,
                "time_ms": path["time"],
                "time_minutes": path["time"] / 60000,
                "time_hours": path["time"] / 3600000,
                "start_point": start,
                "end_point": end,
                "vehicle": vehicle,
                "calculated_at": datetime.now().isoformat()
            }
            
            if calc_points:
                result["points"] = path.get("points", {}).get("coordinates", [])
                result["instructions"] = path.get("instructions", [])
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get route: {e}")
            if self.allow_fallback:
                logger.warning("Using fallback route estimation because GraphHopper is unavailable")
                return self._build_fallback_route(start, end, vehicle, calc_points)
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid response from GraphHopper: {e}")
            raise
    
    def get_distance_matrix(
        self,
        points: List[Tuple[float, float]],
        vehicle: str = "car"
    ) -> Dict:
        """
        Calculate distance matrix for multiple points
        More efficient than calling get_route multiple times
        
        Args:
            points: List of (latitude, longitude) tuples
            vehicle: Transportation mode
        
        Returns:
            dict: Distance and time matrices
            
        Example:
            >>> client = GraphHopperClient()
            >>> points = [
            ...     (-6.1754, 106.8272),  # Point A
            ...     (-6.2088, 106.8456),  # Point B
            ...     (-6.1944, 106.8229),  # Point C
            ... ]
            >>> matrix = client.get_distance_matrix(points)
            >>> # Distance from point A to point B
            >>> distance_km = matrix['distances'][0][1] / 1000
        """
        url = f"{self.base_url}/matrix"
        
        params = {
            "point": [f"{lat},{lon}" for lat, lon in points],
            "vehicle": vehicle,
            "out_array": ["distances", "times"]
        }
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "distances": data.get("distances", []),  # in meters
                "times": data.get("times", []),  # in milliseconds
                "points": points,
                "vehicle": vehicle,
                "calculated_at": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get distance matrix: {e}")
            if self.allow_fallback:
                logger.warning("Using fallback distance matrix estimation because GraphHopper is unavailable")
                return self._build_fallback_matrix(points, vehicle)
            raise
    
    def get_isochrone(
        self,
        center: Tuple[float, float],
        time_limit: int,
        vehicle: str = "car"
    ) -> Dict:
        """
        Calculate isochrone (reachable area within time limit)
        
        Args:
            center: (latitude, longitude) for center point
            time_limit: Time limit in seconds
            vehicle: Transportation mode
        
        Returns:
            dict: Polygon coordinates representing reachable area
            
        Example:
            >>> client = GraphHopperClient()
            >>> # Get area reachable within 15 minutes from Jakarta center
            >>> area = client.get_isochrone(
            ...     center=(-6.1754, 106.8272),
            ...     time_limit=900,  # 15 minutes
            ...     vehicle="car"
            ... )
        """
        url = f"{self.base_url}/isochrone"
        
        params = {
            "point": f"{center[0]},{center[1]}",
            "time_limit": time_limit,
            "vehicle": vehicle,
            "buckets": 1
        }
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "polygons": data.get("polygons", []),
                "center": center,
                "time_limit": time_limit,
                "vehicle": vehicle,
                "calculated_at": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get isochrone: {e}")
            raise
    
    def optimize_route(
        self,
        depot: Tuple[float, float],
        locations: List[Tuple[float, float]],
        vehicle: str = "car",
        return_to_depot: bool = True
    ) -> Dict:
        """
        Optimize route for multiple locations (Traveling Salesman Problem)
        Requires GraphHopper Premium or self-hosted with optimization enabled
        
        Args:
            depot: Starting point (warehouse/home base)
            locations: List of locations to visit
            vehicle: Transportation mode
            return_to_depot: Whether to return to starting point
        
        Returns:
            dict: Optimized route order and total distance/time
        """
        if not locations:
            return {
                "route_indices": [0],
                "route_points": [depot],
                "total_distance_meters": 0,
                "total_distance_km": 0,
                "total_time_ms": 0,
                "total_time_minutes": 0,
                "vehicle": vehicle,
                "calculated_at": datetime.now().isoformat(),
                "optimization_method": "empty",
            }

        try:
            result = self._optimize_route_vrp(depot, locations, vehicle, return_to_depot)
            result["optimization_method"] = "graphhopper_vrp"
            return result
        except Exception as e:
            logger.warning(f"VRP optimization unavailable, using nearest-neighbor fallback: {e}")
            fallback_result = self._nearest_neighbor_route(depot, locations, vehicle, return_to_depot)
            fallback_result["optimization_method"] = "nearest_neighbor_fallback"
            return fallback_result

    def _optimize_route_vrp(
        self,
        depot: Tuple[float, float],
        locations: List[Tuple[float, float]],
        vehicle: str,
        return_to_depot: bool,
    ) -> Dict:
        """Optimize route using GraphHopper /vrp/optimize and /vrp/solution endpoints."""
        if not self.api_key:
            raise ValueError("GRAPHHOPPER_API_KEY is required for GraphHopper VRP optimization")

        vehicle_type_id = f"type_{vehicle}"
        vehicle_id = f"vehicle_{vehicle}"

        services = []
        for index, (lat, lon) in enumerate(locations, start=1):
            services.append(
                {
                    "id": f"service_{index}",
                    "name": f"stop_{index}",
                    "address": {
                        "location_id": f"loc_{index}",
                        "lat": lat,
                        "lon": lon,
                    },
                }
            )

        payload = {
            "vehicles": [
                {
                    "vehicle_id": vehicle_id,
                    "type_id": vehicle_type_id,
                    "start_address": {
                        "location_id": "depot_start",
                        "lat": depot[0],
                        "lon": depot[1],
                    },
                    "return_to_depot": return_to_depot,
                }
            ],
            "vehicle_types": [{"type_id": vehicle_type_id, "profile": vehicle}],
            "services": services,
        }

        optimize_response = self.session.post(
            f"{self.base_url}/vrp/optimize",
            json=payload,
            timeout=60,
        )
        optimize_response.raise_for_status()
        optimize_data = optimize_response.json()

        job_id = optimize_data.get("job_id")
        if not job_id:
            raise ValueError("GraphHopper VRP optimize response does not contain job_id")

        solution_data = self._poll_vrp_solution(job_id)
        return self._parse_vrp_solution(solution_data, depot, locations)

    def _poll_vrp_solution(self, job_id: str, timeout_seconds: int = 120) -> Dict:
        """Poll GraphHopper VRP solution endpoint until finished."""
        deadline = time.time() + timeout_seconds
        last_status = None

        while time.time() < deadline:
            response = self.session.get(f"{self.base_url}/vrp/solution/{job_id}", timeout=30)
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            last_status = status

            if status == "finished":
                return data
            if status in {"failed", "timeout"}:
                raise ValueError(f"GraphHopper VRP job ended with status: {status}")

            time.sleep(2)

        raise TimeoutError(f"Timed out waiting for VRP solution (last status: {last_status})")

    def _parse_vrp_solution(self, solution_data: Dict, depot: Tuple[float, float], locations: List[Tuple[float, float]]) -> Dict:
        """Convert GraphHopper VRP solution into route index format used by this project."""
        solution = solution_data.get("solution", {})
        routes = solution.get("routes", [])
        if not routes:
            raise ValueError("GraphHopper VRP response has no routes")

        activities = routes[0].get("activities", [])
        route_indices = [0]

        for activity in activities:
            activity_type = activity.get("type")
            if activity_type not in {"service", "pickup", "delivery"}:
                continue

            location_id = activity.get("location_id", "")
            if location_id.startswith("loc_"):
                try:
                    loc_index = int(location_id.split("_")[1])
                    route_indices.append(loc_index)
                except (IndexError, ValueError):
                    continue

        if not route_indices or route_indices[0] != 0:
            route_indices = [0] + route_indices

        if route_indices[-1] != 0:
            route_indices.append(0)

        all_points = [depot] + locations
        return {
            "route_indices": route_indices,
            "route_points": [all_points[i] for i in route_indices],
            "total_distance_meters": solution.get("distance", 0),
            "total_distance_km": solution.get("distance", 0) / 1000,
            "total_time_ms": solution.get("time", 0),
            "total_time_minutes": solution.get("time", 0) / 60000,
            "vehicle": routes[0].get("vehicle_id", "unknown"),
            "calculated_at": datetime.now().isoformat(),
        }
    
    def _nearest_neighbor_route(
        self,
        depot: Tuple[float, float],
        locations: List[Tuple[float, float]],
        vehicle: str = "car",
        return_to_depot: bool = True
    ) -> Dict:
        """
        Simple nearest neighbor algorithm for route optimization
        Not optimal but works without premium features
        """
        all_points = [depot] + locations
        matrix = self.get_distance_matrix(all_points, vehicle)
        
        distances = matrix['distances']
        times = matrix['times']
        
        # Greedy nearest neighbor
        visited = [False] * len(locations)
        route = [0]  # Start at depot
        current = 0
        total_distance = 0
        total_time = 0
        
        for _ in range(len(locations)):
            nearest_idx = None
            nearest_dist = float('inf')
            
            for i in range(len(locations)):
                if not visited[i]:
                    actual_idx = i + 1  # +1 because depot is at index 0
                    dist = distances[current][actual_idx]
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest_idx = i
            
            if nearest_idx is not None:
                visited[nearest_idx] = True
                actual_idx = nearest_idx + 1
                route.append(actual_idx)
                total_distance += distances[current][actual_idx]
                total_time += times[current][actual_idx]
                current = actual_idx
        
        # Return to depot if required
        if return_to_depot:
            route.append(0)
            total_distance += distances[current][0]
            total_time += times[current][0]
        
        return {
            "route_indices": route,
            "route_points": [all_points[i] for i in route],
            "total_distance_meters": total_distance,
            "total_distance_km": total_distance / 1000,
            "total_time_ms": total_time,
            "total_time_minutes": total_time / 60000,
            "vehicle": vehicle,
            "calculated_at": datetime.now().isoformat()
        }


def calculate_route_distance(start_lat: float, start_lon: float, 
                            end_lat: float, end_lon: float,
                            vehicle: str = "car") -> Tuple[float, float]:
    """
    Simple function to calculate distance and time between two points
    
    Args:
        start_lat, start_lon: Starting coordinates
        end_lat, end_lon: Ending coordinates
        vehicle: Transportation mode
    
    Returns:
        tuple: (distance_km, time_minutes)
    """
    client = GraphHopperClient()
    route = client.get_route((start_lat, start_lon), (end_lat, end_lon), vehicle)
    return route['distance_km'], route['time_minutes']


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    client = GraphHopperClient()
    
    # Health check
    if client.health_check():
        print("✅ GraphHopper is healthy")
    else:
        print("❌ GraphHopper is not available")
        exit(1)
    
    # Example: Jakarta to Bandung
    print("\n--- Route Calculation ---")
    route = client.get_route(
        start=(-6.2088, 106.8456),  # Jakarta
        end=(-6.9175, 107.6191),    # Bandung
        vehicle="car"
    )
    print(f"Distance: {route['distance_km']:.2f} km")
    print(f"Duration: {route['time_minutes']:.1f} minutes ({route['time_hours']:.2f} hours)")
    
    # Example: Distance matrix for 3 cities
    print("\n--- Distance Matrix ---")
    cities = [
        (-6.2088, 106.8456),  # Jakarta
        (-6.9175, 107.6191),  # Bandung
        (-7.2575, 112.7521),  # Surabaya
    ]
    matrix = client.get_distance_matrix(cities)
    print("Distance matrix (km):")
    for i, row in enumerate(matrix['distances']):
        print(f"City {i}: {[f'{d/1000:.1f}' for d in row]}")
