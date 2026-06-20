"""Tests for weather_server format functions (pure, no mocking needed)."""

from src.mcp_client_service.server.weather_server import format_weather_data, format_forecast_data


class TestFormatWeatherData:
    """Tests for format_weather_data — formats current weather response."""

    def test_formats_basic_weather(self):
        data = {
            "name": "Beijing",
            "main": {"temp": 25.0, "humidity": 60, "pressure": 1013},
            "weather": [{"description": "clear sky"}],
            "wind": {"speed": 3.5},
        }
        result = format_weather_data(data)
        assert "Beijing" in result
        assert "25.0" in result
        assert "60" in result
        assert "clear sky" in result

    def test_formats_weather_with_multiple_conditions(self):
        data = {
            "name": "Shanghai",
            "main": {"temp": 18.5, "humidity": 80, "pressure": 1010},
            "weather": [{"description": "light rain"}, {"description": "mist"}],
            "wind": {"speed": 5.2},
        }
        result = format_weather_data(data)
        assert "Shanghai" in result
        assert "light rain" in result

    def test_handles_missing_wind(self):
        data = {
            "name": "Tokyo",
            "main": {"temp": 20.0, "humidity": 50, "pressure": 1015},
            "weather": [{"description": "sunny"}],
        }
        result = format_weather_data(data)
        assert "Tokyo" in result
        assert "20.0" in result


class TestFormatForecastData:
    """Tests for format_forecast_data — formats multi-day forecast response."""

    def test_formats_single_day_forecast(self):
        data = {
            "city": {"name": "Beijing"},
            "list": [
                {
                    "dt": 1700000000,
                    "main": {"temp": 22.0, "humidity": 55},
                    "weather": [{"description": "partly cloudy"}],
                    "dt_txt": "2024-06-19 12:00:00",
                }
            ],
        }
        result = format_forecast_data(data)
        assert "Beijing" in result
        assert "22.0" in result
        assert "partly cloudy" in result

    def test_formats_multiple_days(self):
        data = {
            "city": {"name": "Shenzhen"},
            "list": [
                {
                    "dt": 1700000000,
                    "main": {"temp": 26.0, "humidity": 70},
                    "weather": [{"description": "sunny"}],
                    "dt_txt": "2024-06-19 12:00:00",
                },
                {
                    "dt": 1700086400,
                    "main": {"temp": 24.0, "humidity": 75},
                    "weather": [{"description": "rain"}],
                    "dt_txt": "2024-06-20 12:00:00",
                },
                {
                    "dt": 1700172800,
                    "main": {"temp": 23.0, "humidity": 80},
                    "weather": [{"description": "overcast"}],
                    "dt_txt": "2024-06-21 12:00:00",
                },
            ],
        }
        result = format_forecast_data(data, days=3)
        assert "Shenzhen" in result
        assert "26.0" in result
        assert "24.0" in result
        assert "23.0" in result

    def test_respects_days_parameter(self):
        data = {
            "city": {"name": "Guangzhou"},
            "list": [
                {
                    "dt": 1700000000,
                    "main": {"temp": 28.0, "humidity": 65},
                    "weather": [{"description": "hot"}],
                    "dt_txt": "2024-06-19 12:00:00",
                },
                {
                    "dt": 1700086400,
                    "main": {"temp": 27.0, "humidity": 68},
                    "weather": [{"description": "warm"}],
                    "dt_txt": "2024-06-20 12:00:00",
                },
            ],
        }
        result = format_forecast_data(data, days=1)
        assert "28.0" in result
        # With days=1 only first entry should appear
        assert "27.0" not in result

    def test_handles_empty_forecast_list(self):
        data = {"city": {"name": "Beijing"}, "list": []}
        result = format_forecast_data(data)
        assert "Beijing" in result
