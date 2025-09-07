from typing import Dict, List, Optional
from datetime import datetime


class DataStorage:
    """Simple in-memory storage for demo - replace with real DB in production"""

    def __init__(self):
        self.prices = {}
        self.loads = {}
        self.runs = []

    def save_prices(self, zone_eic: str, date_str: str, prices: List[Dict]):
        """Save price data"""
        key = f"{zone_eic}_{date_str}"
        self.prices[key] = prices

    def get_prices(self, zone_eic: str, date_str: str) -> Optional[List[Dict]]:
        """Get price data"""
        key = f"{zone_eic}_{date_str}"
        return self.prices.get(key)

    def save_load(self, zone_eic: str, date_str: str, loads: List[Dict]):
        """Save load data"""
        key = f"{zone_eic}_{date_str}"
        self.loads[key] = loads

    def get_load(self, zone_eic: str, date_str: str) -> Optional[List[Dict]]:
        """Get load data"""
        key = f"{zone_eic}_{date_str}"
        return self.loads.get(key)

    def save_run(self, run_data: Dict):
        """Save optimization run"""
        run_data['timestamp'] = datetime.now().isoformat()
        self.runs.append(run_data)
        return len(self.runs) - 1


# Global storage instance
storage = DataStorage()
