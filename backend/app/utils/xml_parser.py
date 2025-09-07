import xmltodict
from typing import Dict, List, Any
from datetime import datetime, timedelta
import pandas as pd


def parse_day_ahead_prices(xml_content: str) -> List[Dict[str, Any]]:
    """Parse ENTSO-E day-ahead price XML response"""
    try:
        data = xmltodict.parse(xml_content)

        # Navigate to TimeSeries in the XML structure
        time_series = data.get('Publication_MarketDocument', {}).get('TimeSeries', [])
        if not isinstance(time_series, list):
            time_series = [time_series]

        prices = []
        for ts in time_series:
            period = ts.get('Period', {})
            points = period.get('Point', [])
            if not isinstance(points, list):
                points = [points]

            start_time = datetime.fromisoformat(period.get('timeInterval', {}).get('start', '').replace('Z', '+00:00'))

            for point in points:
                position = int(point.get('position', 0))
                price = float(point.get('price.amount', 0))
                hour_time = start_time + timedelta(hours=position - 1)

                prices.append({
                    'hour_utc': hour_time,
                    'price_eur_mwh': price,
                    'price_eur_kwh': price / 1000
                })

        return prices
    except Exception as e:
        print(f"Error parsing prices XML: {e}")
        return []


def parse_actual_load(xml_content: str) -> List[Dict[str, Any]]:
    """Parse ENTSO-E actual load XML response"""
    try:
        data = xmltodict.parse(xml_content)

        time_series = data.get('GL_MarketDocument', {}).get('TimeSeries', [])
        if not isinstance(time_series, list):
            time_series = [time_series]

        loads = []
        for ts in time_series:
            period = ts.get('Period', {})
            points = period.get('Point', [])
            if not isinstance(points, list):
                points = [points]

            start_time = datetime.fromisoformat(period.get('timeInterval', {}).get('start', '').replace('Z', '+00:00'))

            for point in points:
                position = int(point.get('position', 0))
                quantity = float(point.get('quantity', 0))
                hour_time = start_time + timedelta(hours=position - 1)

                loads.append({
                    'hour_utc': hour_time,
                    'load_mw': quantity
                })

        return loads
    except Exception as e:
        print(f"Error parsing load XML: {e}")
        return []
