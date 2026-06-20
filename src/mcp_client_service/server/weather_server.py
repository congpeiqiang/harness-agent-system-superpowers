"""Weather MCP Server with SSE transport.

Provides two tools:
- get_weather: Query current weather for a city
- get_weather_forecast: Query weather forecast for a city
"""

import os
from collections import OrderedDict

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

# Server initialization
app = FastMCP("weather-server")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5"


def format_weather_data(data: dict) -> str:
    """Format current weather API response into readable text.

    Args:
        data: OpenWeatherMap current weather response dict.

    Returns:
        Formatted weather string with city, temperature, conditions, humidity, and wind.
    """
    name = data.get("name", "Unknown")
    main = data.get("main", {})
    temp = main.get("temp", 0)
    feels_like = main.get("feels_like", temp)
    humidity = main.get("humidity", 0)

    weather_list = data.get("weather", [])
    description = weather_list[0].get("description", "") if weather_list else ""

    wind = data.get("wind", {})
    wind_speed = wind.get("speed", 0)

    lines = [
        f"城市: {name}",
        f"温度: {temp}°C (体感 {feels_like}°C)",
        f"天气: {description}",
        f"湿度: {humidity}%",
        f"风力: {wind_speed} m/s",
    ]
    return "\n".join(lines)


def format_forecast_data(data: dict, days: int | None = None) -> str:
    """Format forecast API response into readable text.

    Args:
        data: OpenWeatherMap forecast response dict with 'city' and 'list' keys.
        days: Number of unique days to include. If None, include all entries.

    Returns:
        Formatted forecast string with city name and per-entry weather lines.
    """
    city_info = data.get("city", {})
    city_name = city_info.get("name", "Unknown")

    lines = [f"天气预报 ({city_name}):"]

    entries = data.get("list", [])

    if days is not None:
        # Group entries by unique date and only include the first N unique dates
        unique_dates: OrderedDict[str, list] = OrderedDict()
        for item in entries:
            dt_txt = item.get("dt_txt", "")
            date_part = dt_txt.split(" ")[0] if dt_txt else ""
            if date_part not in unique_dates:
                unique_dates[date_part] = []
            unique_dates[date_part].append(item)
            if len(unique_dates) > days:
                break
        # Only keep entries from the first `days` unique dates
        filtered_entries = []
        for date_entries in list(unique_dates.values())[:days]:
            filtered_entries.extend(date_entries)
        entries = filtered_entries

    for item in entries:
        dt_txt = item.get("dt_txt", "")
        main = item.get("main", {})
        temp = main.get("temp", 0)
        weather_list = item.get("weather", [])
        description = weather_list[0].get("description", "") if weather_list else ""
        lines.append(f"  {dt_txt}: {temp}°C {description}")

    return "\n".join(lines)


@app.tool()
async def get_weather(city: str) -> list[TextContent]:
    """查询指定城市的实时天气信息。

    Args:
        city: 城市名称，例如 "Beijing", "Shanghai"
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/weather",
            params={
                "q": city,
                "appid": WEATHER_API_KEY,
                "units": "metric",
                "lang": "zh_cn",
            },
        )
        response.raise_for_status()
        return [TextContent(type="text", text=format_weather_data(response.json()))]


@app.tool()
async def get_weather_forecast(city: str, days: int = 3) -> list[TextContent]:
    """查询指定城市未来几天的天气预报。

    Args:
        city: 城市名称，例如 "Beijing", "Shanghai"
        days: 预报天数，默认3天
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/forecast",
            params={
                "q": city,
                "appid": WEATHER_API_KEY,
                "units": "metric",
                "lang": "zh_cn",
                "cnt": days * 8,
            },
        )
        response.raise_for_status()
        return [
            TextContent(
                type="text", text=format_forecast_data(response.json(), days=days)
            )
        ]


# SSE transport - Starlette app
starlette_app = app.sse_app()
