# Weatherly — Weather Forecast Dashboard

A Python 3.10+ desktop micro-project built with Tkinter and the OpenWeatherMap REST API. The core dashboard follows the supplied *Micro Project Report: Weather Forecast Dashboard using REST API and Tkinter GUI*: city search, current conditions, five-day forecast, Celsius/Fahrenheit conversion, forecast statistics, Matplotlib temperature chart, search history, favourites, automatic refresh, input validation, custom exceptions and background-thread API calls.

An additional **Weather Day Planner** tab is included as an extension: save indoor/outdoor activities with a date and time, check the matching forecast, and receive a pop-up reminder 30 minutes before an activity (while the app is open). Outdoor rain/storm/snow and high-heat conditions produce warnings. Planner entries are stored in `data/schedule.json`.

## 1. OpenWeatherMap API key

Create a free API key at [OpenWeatherMap](https://openweathermap.org/api). Open `config.json` and replace `YOUR_OPENWEATHERMAP_API_KEY` with your key. Keep the key private; do not upload it to GitHub.

## 2. Run on macOS

```bash
cd weather_dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Tkinter is included with most Python installations. If your Python build does not include Tkinter, install a Python distribution that includes Tcl/Tk.

## 3. Project structure

```text
weather_dashboard/
├── app.py                  # WeatherApp Tkinter GUI + planner tab
├── exceptions.py           # WeatherError hierarchy
├── config.json             # API key, default city, unit, refresh interval
├── requirements.txt
├── models/
│   └── weather.py          # WeatherData and ForecastDay
├── services/
│   ├── api_client.py       # BaseAPIClient and WeatherAPIClient
│   ├── analyzer.py         # WeatherAnalyzer (map/filter/reduce/lambda)
│   ├── chart.py            # ChartPlotter (Matplotlib)
│   └── storage.py          # JSON history and favourites
└── data/
    ├── history.json
    ├── favourites.json
    └── schedule.json       # created when planner entries are saved
```

## 4. Features and concepts

- REST API: OpenWeatherMap Current Weather and 5-day/3-hour Forecast endpoints.
- OOP: classes, constructors, encapsulation, inheritance, polymorphism, abstraction (`abc.ABC`), composition and custom exceptions.
- Functional Python: `map`, `filter`, `reduce`, `lambda`, comprehensions and `sorted`.
- Concurrency: `threading.Thread` for HTTP calls and `queue.Queue` to update Tkinter safely on its main thread.
- Persistence: JSON files for history, favourites, settings and activity schedules (no database, as specified in the report).
- Visualization: Matplotlib chart embedded in Tkinter.
- Errors: empty/invalid city, unknown city, invalid API key, API and network failures are handled with clear messages.

## Notes

- Internet access and a valid OpenWeatherMap API key are required.
- OpenWeatherMap's forecast endpoint provides 3-hour forecast slots; the app groups these into up to five calendar days.
- Weather warnings are based on forecast descriptions and temperature thresholds, not official severe-weather alerts. The reminder feature runs only while the desktop app remains open.
- The five-day forecast shown by this API is not an hourly planner; an activity can only be checked if its date appears in the returned forecast.
