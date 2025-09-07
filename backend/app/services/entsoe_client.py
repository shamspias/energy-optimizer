import httpx
from datetime import datetime, timedelta
from typing import Dict, List
from app.config import settings
from app.utils.xml_parser import parse_day_ahead_prices, parse_actual_load
import random
import json
import os


class EntsoeClient:
    def __init__(self):
        self.base_url = settings.entsoe_base_url
        self.token = settings.entsoe_api_token

    # ---------- helpers for mock files ----------
    def _mock_file_path(self, zone_eic: str, date_str: str, kind: str) -> str:
        """
        kind: "prices" or "loads"
        filename: {zone}_{date}.{kind}.json  e.g. 10YNL----------L_2025-09-05.prices.json
        """
        fname = f"{zone_eic}_{date_str}.{kind}.json"
        return os.path.join(settings.mock_data_dir, fname)

    def _load_mock_json(self, path: str) -> List[Dict]:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Coerce hour_utc back to datetime objects if strings
        for d in data:
            if isinstance(d.get("hour_utc"), str):
                d["hour_utc"] = datetime.fromisoformat(d["hour_utc"].replace("Z", "+00:00"))
        return data

    # ---------- generators (fallback if file missing) ----------
    def _generate_mock_prices(self, date: datetime) -> List[Dict]:
        prices = []
        base_price = 80  # €/MWh
        rng = random.Random(42 + int(date.strftime("%Y%m%d")))  # deterministic-ish per date

        for hour in range(24):
            hour_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            if 0 <= hour <= 5:
                multiplier = 0.7 + rng.uniform(-0.1, 0.1)
            elif 6 <= hour <= 9:
                multiplier = 1.2 + rng.uniform(-0.1, 0.2)
            elif 10 <= hour <= 16:
                multiplier = 1.0 + rng.uniform(-0.1, 0.1)
            elif 17 <= hour <= 21:
                multiplier = 1.3 + rng.uniform(-0.1, 0.2)
            else:
                multiplier = 0.9 + rng.uniform(-0.1, 0.1)
            price = base_price * multiplier
            prices.append({
                'hour_utc': hour_time,
                'price_eur_mwh': round(price, 2),
                'price_eur_kwh': round(price / 1000, 5)
            })
        return prices

    def _generate_mock_load(self, date: datetime) -> List[Dict]:
        loads = []
        base_load = 12000  # MW
        rng = random.Random(99 + int(date.strftime("%Y%m%d")))
        for hour in range(24):
            hour_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            if 0 <= hour <= 5:
                multiplier = 0.6 + rng.uniform(-0.05, 0.05)
            elif 6 <= hour <= 9:
                multiplier = 0.9 + rng.uniform(-0.05, 0.1)
            elif 10 <= hour <= 17:
                multiplier = 1.0 + rng.uniform(-0.05, 0.05)
            elif 18 <= hour <= 21:
                multiplier = 1.1 + rng.uniform(-0.05, 0.1)
            else:
                multiplier = 0.8 + rng.uniform(-0.05, 0.05)
            load = base_load * multiplier
            loads.append({
                'hour_utc': hour_time,
                'load_mw': round(load, 2)
            })
        return loads

    # ---------- public API ----------
    async def fetch_day_ahead_prices(self, zone_eic: str, date_str: str) -> List[Dict]:
        date = datetime.strptime(date_str, "%Y-%m-%d")

        # MOCK mode via file or generator
        if settings.use_mock_data or not self.token:
            if settings.mock_source.lower() == "file":
                path = self._mock_file_path(zone_eic, date_str, "prices")
                data = self._load_mock_json(path)
                if data:
                    return data
                # fallback to generator if file missing
            return self._generate_mock_prices(date)

        # LIVE mode (unchanged)
        try:
            period_start = (date - timedelta(hours=2)).strftime("%Y%m%d%H%M")
            period_end = (date + timedelta(hours=22)).strftime("%Y%m%d%H%M")
            params = {
                "documentType": "A44",
                "in_Domain": zone_eic,
                "out_Domain": zone_eic,
                "periodStart": period_start,
                "periodEnd": period_end,
                "securityToken": self.token
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.base_url, params=params, timeout=30.0)
                if resp.status_code == 200:
                    prices = parse_day_ahead_prices(resp.text)
                    return [p for p in prices if p['hour_utc'].date() == date.date()]
                return self._generate_mock_prices(date)
        except Exception:
            return self._generate_mock_prices(date)

    async def fetch_actual_load(self, zone_eic: str, date_str: str) -> List[Dict]:
        date = datetime.strptime(date_str, "%Y-%m-%d")

        # MOCK mode via file or generator
        if settings.use_mock_data or not self.token:
            if settings.mock_source.lower() == "file":
                path = self._mock_file_path(zone_eic, date_str, "loads")
                data = self._load_mock_json(path)
                if data:
                    return data
            return self._generate_mock_load(date)

        # LIVE mode (unchanged)
        try:
            period_start = (date - timedelta(hours=2)).strftime("%Y%m%d%H%M")
            period_end = (date + timedelta(hours=22)).strftime("%Y%m%d%H%M")
            params = {
                "documentType": "A65",
                "processType": "A16",
                "outBiddingZone_Domain": zone_eic,
                "periodStart": period_start,
                "periodEnd": period_end,
                "securityToken": self.token
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.base_url, params=params, timeout=30.0)
                if resp.status_code == 200:
                    loads = parse_actual_load(resp.text)
                    return [l for l in loads if l['hour_utc'].date() == date.date()]
                return self._generate_mock_load(date)
        except Exception as e:
            print("error: ", str(e))
            return self._generate_mock_load(date)
