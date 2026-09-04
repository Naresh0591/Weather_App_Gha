import os
import socket
from datetime import datetime, timezone

import requests
from flask import Flask, render_template, request

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Hyderabad")

# WMO weather codes -> (description, emoji)
WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    61: ("Slight rain", "🌦️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    71: ("Slight snow", "🌨️"),
    73: ("Moderate snow", "🌨️"),
    75: ("Heavy snow", "❄️"),
    80: ("Rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


def get_weather(city):
    """Fetch current weather for a city name. Returns dict or None on failure."""
    try:
        geo_resp = requests.get(
            GEOCODE_URL, params={"name": city, "count": 1}, timeout=5
        )
        geo_resp.raise_for_status()
        results = geo_resp.json().get("results")
        if not results:
            return None

        place = results[0]
        lat, lon = place["latitude"], place["longitude"]

        forecast_resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,apparent_temperature",
                "timezone": "auto",
            },
            timeout=5,
        )
        forecast_resp.raise_for_status()
        current = forecast_resp.json().get("current", {})

        code = current.get("weather_code", 0)
        description, emoji = WEATHER_CODES.get(code, ("Unknown", "🌡️"))

        return {
            "city": place.get("name", city),
            "region": place.get("admin1", ""),
            "country": place.get("country", ""),
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "description": description,
            "emoji": emoji,
        }
    except requests.RequestException:
        return None


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        city = request.args.get("city", DEFAULT_CITY).strip() or DEFAULT_CITY
        weather = get_weather(city)
        return render_template(
            "index.html",
            city_query=city,
            weather=weather,
            hostname=socket.gethostname(),
            image_tag=os.getenv("IMAGE_TAG", "local"),
            server_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=True)
