class WeatherData:
    def __init__(self, city, country, temp_c, feels_like_c, humidity, pressure,
                 wind_speed, condition, icon=""):
        self.city, self.country = city, country
        self.__temp_c = float(temp_c)
        self.feels_like_c = float(feels_like_c)
        self.humidity, self.pressure = int(humidity), int(pressure)
        self.wind_speed, self.condition, self.icon = float(wind_speed), condition, icon

    @property
    def temp_c(self): return self.__temp_c

    @staticmethod
    def convert(temp_c, unit="C"):
        return round(temp_c * 9 / 5 + 32, 1) if unit == "F" else round(temp_c, 1)

    def describe(self): return f"{self.condition}, {self.temp_c:.1f} °C"
    def __str__(self): return f"{self.city}: {self.describe()}"
    def __eq__(self, other): return isinstance(other, WeatherData) and self.city == other.city and self.temp_c == other.temp_c

class ForecastDay(WeatherData):
    def __init__(self, date, temp_min_c, temp_max_c, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date, self.temp_min_c, self.temp_max_c = date, float(temp_min_c), float(temp_max_c)
    def describe(self): return f"{self.condition}: {self.temp_min_c:.1f}° / {self.temp_max_c:.1f}°C"
