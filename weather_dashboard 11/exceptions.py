class WeatherError(Exception):
    """Base application error."""

class InvalidCityError(WeatherError): pass
class CityNotFoundError(WeatherError): pass
class InvalidAPIKeyError(WeatherError): pass
class NetworkError(WeatherError): pass
class APIError(WeatherError): pass
