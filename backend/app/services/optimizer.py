from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from app.models.optimization import ShiftHour


class LoadOptimizer:
    def __init__(self):
        self.price_data = {}

    def set_price_data(self, zone_eic: str, date_str: str, prices: List[Dict]):
        """Store price data for optimization"""
        key = f"{zone_eic}_{date_str}"
        self.price_data[key] = prices

    def optimize(
            self,
            zone_eic: str,
            date_str: str,
            kwh_flexible: float,
            max_shift_hours: int,
            objective: str = "min_cost"
    ) -> Dict[str, Any]:
        """Optimize load shifting based on prices"""

        key = f"{zone_eic}_{date_str}"
        prices = self.price_data.get(key, [])

        if not prices:
            raise ValueError(f"No price data available for {zone_eic} on {date_str}")

        # Sort hours by price
        sorted_prices = sorted(prices, key=lambda x: x['price_eur_kwh'])

        # Select cheapest hours for shifting
        selected_hours = sorted_prices[:max_shift_hours]

        # Distribute load evenly across selected hours
        kwh_per_hour = kwh_flexible / max_shift_hours

        schedule = []
        optimized_cost = 0

        for hour_data in selected_hours:
            shift_hour = ShiftHour(
                hour_utc=hour_data['hour_utc'],
                shift_kwh=round(kwh_per_hour, 2),
                price_eur_kwh=hour_data['price_eur_kwh']
            )
            schedule.append(shift_hour)
            optimized_cost += kwh_per_hour * hour_data['price_eur_kwh']

        # Calculate baseline cost (average price)
        avg_price = sum(p['price_eur_kwh'] for p in prices) / len(prices)
        baseline_cost = kwh_flexible * avg_price

        # Calculate savings
        savings = baseline_cost - optimized_cost
        savings_percent = (savings / baseline_cost * 100) if baseline_cost > 0 else 0

        return {
            'baseline_cost_eur': round(baseline_cost, 2),
            'optimized_cost_eur': round(optimized_cost, 2),
            'savings_eur': round(savings, 2),
            'savings_percent': round(savings_percent, 1),
            'schedule': schedule,
            'price_curve': prices
        }
