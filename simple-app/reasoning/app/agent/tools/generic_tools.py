import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from datetime import datetime
from agent_framework import observability_decorator
import yfinance as yf

@observability_decorator(name="get_weather_by_location")
def get_current_weather(location: str) -> str:
    """
    Get the current weather for a given location.
    
    Args:
    location (str): The name of the location or address.
    
    Returns:
    dict: A dictionary containing weather information, or None if there's an error.
    """
    # First, get the latitude and longitude
    geolocator = Nominatim(user_agent="weather_app")
    
    try:
        # Attempt to geocode the location
        location_info = geolocator.geocode(location, timeout=10)
        
        if not location_info:
            print(f"Location not found: {location}")
            return None
        
        latitude, longitude = location_info.latitude, location_info.longitude
        
        # Now, fetch the weather data
        base_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
            "temperature_unit": "celsius",
            "windspeed_unit": "kmh",
            "precipitation_unit": "mm"
        }
        
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            current_weather = data["current_weather"]
            
            # Add location information to the weather data
            current_weather["location"] = location_info.address
            current_weather["latitude"] = latitude
            current_weather["longitude"] = longitude

            out = ''
            out += f"Weather for {current_weather['location']}: \n"
            out += f"Temperature: {current_weather['temperature']}°C \n"
            out += f"Wind speed: {current_weather['windspeed']} km/h \n"
            out += f"Wind direction: {current_weather['winddirection']}° \n"
            
            return out
        else:
            print(f"Error fetching weather data: HTTP {response.status_code}")
            return None
    
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Error geocoding {location}: {str(e)}")
        return None
    except requests.RequestException as e:
        print(f"Error fetching weather data: {str(e)}")
        return None

@observability_decorator(name="get_current_time")
def get_current_time() -> str:
    """
    Get the current date and time as a formatted string.

    This function retrieves the current date and time using the datetime module
    and formats it as a string.

    Returns:
        str: A string representing the current date and time in the format:
             "YYYY-MM-DD HH:MM:SS"

    Example:
        >>> current_time = get_current_time()
        >>> print(f"The current time is: {current_time}")
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@observability_decorator(name="get_stock_price")
def get_stock_price(symbol: str) -> str:
    """
    Get the current stock price for a given symbol.
    
    Args:
    symbol (str): The stock symbol (e.g., AAPL for Apple).
    
    Returns:
    str: A string containing stock price information, or None if there's an error.
    """
    
    try:
        stock = yf.Ticker(symbol)
        print(stock.info)
        current_price = stock.info['currentPrice']
        currency = stock.info['currency']
        out = ''
        out += f"The current market price of {symbol} is: {current_price} \n"
        return out

    except Exception as e:
        print(f"Error fetching stock data: {str(e)}")
        return None