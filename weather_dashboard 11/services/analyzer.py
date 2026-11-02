from functools import reduce
class WeatherAnalyzer:
    def __init__(self, days): self.days = days
    def average(self): return round(reduce(lambda a,b: a+b, map(lambda d:d.temp_c,self.days))/len(self.days),1) if self.days else 0
    def maximum(self): return max(map(lambda d:d.temp_max_c,self.days), default=0)
    def minimum(self): return min(map(lambda d:d.temp_min_c,self.days), default=0)
    def hot_days(self, limit=30): return list(filter(lambda d:d.temp_max_c >= limit,self.days))
    def trend(self):
        if len(self.days)<2:return "Stable"
        delta=self.days[-1].temp_c-self.days[0].temp_c
        return "Warming" if delta>1 else "Cooling" if delta < -1 else "Stable"
    def summary(self): return f"5-day average {self.average()}°C   •   Min {self.minimum():.1f}°C   •   Max {self.maximum():.1f}°C   •   {self.trend()} trend"
