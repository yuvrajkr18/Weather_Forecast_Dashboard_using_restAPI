from abc import ABC, abstractmethod
import re, requests
from collections import defaultdict
from datetime import datetime
from models.weather import WeatherData, ForecastDay
from exceptions import InvalidCityError, CityNotFoundError, InvalidAPIKeyError, NetworkError, APIError

BASE = "https://api.openweathermap.org/data/2.5"
class BaseAPIClient(ABC):
    @abstractmethod
    def fetch_current(self, city): pass
    @abstractmethod
    def fetch_forecast(self, city): pass

class WeatherAPIClient(BaseAPIClient):
    def __init__(self, api_key, timeout=12):
        self.__api_key, self.timeout = api_key.strip(), timeout

    @staticmethod
    def validate_city(city):
        city = city.strip()
        if not re.fullmatch(r"[A-Za-z .'-]{2,60}", city): raise InvalidCityError("Enter a valid city name (letters, spaces, . ' -).")
        return city

    def _get(self, endpoint, city):
        if not self.__api_key or self.__api_key == "YOUR_OPENWEATHERMAP_API_KEY":
            raise InvalidAPIKeyError("Add your OpenWeatherMap API key in config.json.")
        try:
            r = requests.get(f"{BASE}/{endpoint}", params={"q": city, "appid": self.__api_key, "units": "metric"}, timeout=self.timeout)
        except requests.RequestException as e: raise NetworkError(f"Network error: {e}")
        if r.status_code == 401: raise InvalidAPIKeyError("Invalid API key. Check config.json.")
        if r.status_code == 404: raise CityNotFoundError(f"City '{city}' was not found.")
        if r.status_code != 200: raise APIError(f"Weather service error ({r.status_code}).")
        try: return r.json()
        except ValueError: raise APIError("The weather service returned invalid JSON.")

    def fetch_current(self, city):
        city = self.validate_city(city); d = self._get("weather", city)
        return WeatherData(d["name"], d.get("sys", {}).get("country", ""), d["main"]["temp"], d["main"]["feels_like"], d["main"]["humidity"], d["main"]["pressure"], d["wind"].get("speed", 0), d["weather"][0]["description"].title(), d["weather"][0].get("icon", ""))

    def fetch_icon(self, icon_code):
        """Download an optional OpenWeatherMap PNG icon as a Pillow image."""
        if not icon_code: return None
        try:
            from io import BytesIO
            from PIL import Image
            response = requests.get(f"https://openweathermap.org/img/wn/{icon_code}@2x.png", timeout=8)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGBA")
        except Exception:
            return None

    def fetch_forecast(self, city):
        city = self.validate_city(city); d = self._get("forecast", city)
        groups = defaultdict(list)
        for slot in d.get("list", []): groups[slot["dt_txt"].split()[0]].append(slot)
        result = []
        for date, slots in sorted(groups.items())[:5]:
            temps = [x["main"]["temp"] for x in slots]
            mid = slots[len(slots)//2]; w = mid["weather"][0]
            result.append(ForecastDay(date, min(temps), max(temps), d["city"]["name"], d["city"].get("country", ""), sum(temps)/len(temps), mid["main"]["feels_like"], mid["main"]["humidity"], mid["main"]["pressure"], mid.get("wind", {}).get("speed", 0), w["description"].title(), w.get("icon", "")))
        return result
