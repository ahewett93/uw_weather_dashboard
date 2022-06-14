import numpy as np
import pandas as pd
from datetime import datetime,timedelta
from urllib import parse, request, error
from configparser import ConfigParser
import json
# Constants
BASE_WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
BASE_FORECAST_API_URL = "http://api.openweathermap.org/data/2.5/forecast"

def get_uw_data():
    ''' Uses request to get the past week of obs from the ATG Rooftop Wx station
    Variables:
        start = start date, default is NOW constant
        end = end date, default is THEN constant (1 week before now)

    Returns:
        generator for loading the data into a dataframe.

    '''
    start=datetime.now() - timedelta(weeks=1)
    end=datetime.now() + timedelta(hours=7)
    # Change the date ranges in 'dates' for the ones you're interested in
    dates = pd.date_range(start=start, end=end)
    dates_str = dates.strftime("%Y%m%d")
    url_str = "https://a.atmos.washington.edu/cgi-bin/uw.cgi?"

    for i in range(len(dates)):
        url = url_str + dates_str[i]
        with request.urlopen(url) as f:
            # lop off header
            for header in f :
                if 'knot' in str(header):
                    break
            f.readline()

            data_date = dates[i]

            for record in f:
                fields = record.decode().strip().split()

                if len(fields) != 9:
                    continue

                # parse time and convert to a datetime
                t = datetime.strptime(fields[0], '%H:%M:%S')
                delta = timedelta()

                dt = data_date.replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
                observation_time = dt - delta

                data = {
                    'Time': observation_time,
                    'Relative Humidity': int(fields[1]),
                    'Temperature': int(fields[2]),
                    'Wind Direction': int(fields[3]),
                    'Wind Speed': int(fields[4]),
                    'Gust': int(fields[5]),
                    'Rain': float(fields[6]),
                    'Radiation': float(fields[7]),
                    'Pressure': float(fields[8])
                }
                yield data

def load_uw_data():
    ''' Loads the data from the ATG rooftop by calling the get_uw_data function.
    Also formats the dataframe

    Returns:
        df = dataframe with UW ATG rooftop weather data for the past
        week from the current time

    '''
    df = pd.DataFrame(get_uw_data())
    # Takes 10-min averages by resampling
#     df.index = pd.to_datetime(df.Time)
#     df = df.resample(rule = '10Min').mean()
    # Modify the datetime objects and make a new column for dates.
    df['Time'] = pd.to_datetime(df['Time'])
    # Resample for 30mins to smooth everything out.
    df = df.resample(rule='30Min', on='Time').mean()
    df['Time'] = df.index
    df['Date'] = pd.to_datetime(df['Time']).dt.date
    # Temperature has weird zero values, drop them
    df['Temperature'].replace([0, 0.0], np.nan, inplace=True)

    return df

def get_api_key():
    """Fetch the API key from your configuration file.

    Expects a configuration file named "secrets.ini" with structure:

        [openweather]
        api_key=<YOUR-OPENWEATHER-API-KEY>
    """
    config = ConfigParser()
    config.read("secrets.ini")
    return config["openweather"]["api_key"]

def get_weather_data(query_url):
    """Makes an API request to a URL and returns the data as a Python object.

    Args:
        query_url (str): URL formatted for OpenWeather's city name endpoint

    Returns:
        dict: Weather information for a specific city
    """
    # Makes the HTTP GET request
    try:
        response = request.urlopen(query_url)
    except error.HTTPError as http_error:
        # API key is invalid
        if http_error.code == 401:  # 401 - Unauthorized
            sys.exit("Access denied. Check your API key.")
        # City doesn't exist
        elif http_error.code == 404:  # 404 - Not Found
            sys.exit("Can't find weather data for this city.")
        # Unkown error
        else:
            sys.exit(f"Something went wrong... ({http_error.code})")
    # Extracts the data frm the response
    data = response.read()
    # loads the JSON data
    try:
        return json.loads(data)
    # Bad JSON data
    except json.JSONDecodeError:
        sys.exit("Couldn't read the server response.")

def get_forecast_data(weather_data, imperial=False):
    api_key = get_api_key()
    # Get the coordinates
    lat = weather_data['coord']['lat']
    lon = weather_data['coord']['lon']
    # units
    units = "imperial" if imperial else "metric"
    # MAke the forecast url
    forecast_url = (
        f"{BASE_FORECAST_API_URL}?lat={lat}&lon={lon}"
        f"&units={units}&appid={api_key}"
    )

    # Make the API call
    try:
        response = request.urlopen(forecast_url)
    except error.HTTPError as http_error:
        # API key is invalid
        if http_error.code == 401:  # 401 - Unauthorized
            sys.exit("Forecast: Access denied. Check your API key.")
        # City doesn't exist
        elif http_error.code == 404:  # 404 - Not Found
            sys.exit("Forecast: Can't find forecast data for this city.")
        # Unkown error
        else:
            sys.exit(f"Forecast: Something went wrong... ({http_error.code})")
    # Extracts the data frm the response
    data = response.read()
    # loads the JSON data
    try:
        return json.loads(data)
    # Bad JSON data
    except json.JSONDecodeError:
        sys.exit("Forecast: Couldn't read the server response.")

def get_current_wx(current_data):
    ''' Extracts desired data from the Openweather JSON data containing
    current conditions.

    Variables:
        current_data = the current weather data JSON
    Returns:
        current_wx = dictionary containing extracted data

    '''
    sunset = datetime.fromtimestamp(current_data['sys']['sunset']).strftime("%H:%M")
    sunrise = datetime.fromtimestamp(current_data['sys']['sunrise']).strftime("%H:%M")
    date = datetime.fromtimestamp(current_data['dt']).strftime("%m/%d/%Y")
    time = datetime.fromtimestamp(current_data['dt']).strftime("%H:%M")
    wx = current_data['weather'][0]['description']
    temp = int(np.round(current_data['main']['temp']))
    pressure = current_data['main']['pressure']
    humidity = current_data['main']['humidity']
    wind_speed = int(np.round(current_data['wind']['speed']))
    wind_dir = current_data['wind']['deg']
    clouds = current_data['clouds']['all']

    current_wx = {
        'Sunset': sunset,
        'Sunrise': sunrise,
        'date': date,
        'time': time,
        'wx': wx,
        'temperature': temp,
        'pressure': pressure,
        'humidity': humidity,
        'wind speed': wind_speed,
        'wind dir': wind_dir,
        'clouds': clouds
    }
    return current_wx

def get_forecast_dataframe(forecast_wx):
    '''Takes in the 5 day, 3 hourly forecast JSON data from Openweather
    and unpacks it to make a pandas dataframe

    Variables:
        forecast_data = JSON data returned from API call
    Returns:
        df = pandas dataframe with desired data
    '''
    # Get the datetimes
    dts = [date['dt_txt'] for date in forecast_wx['list']]
    dts = pd.to_datetime(dts)
    dts = dts.strftime('%m/%d/%Y %H:%M')
    # Get the other quantities
    temperature = np.round([date['main']['temp'] for date in forecast_wx['list']])
    temp_min = [date['main']['temp_min'] for date in forecast_wx['list']]
    temp_max = [date['main']['temp_max'] for date in forecast_wx['list']]
    pressure = [date['main']['pressure'] for date in forecast_wx['list']]
    humidity = [date['main']['humidity'] for date in forecast_wx['list']]
    weather = [date['weather'][0]['main'] for date in forecast_wx['list']]
    weather_description = [date['weather'][0]['description'] for date in forecast_wx['list']]
    clouds = [date['clouds']['all'] for date in forecast_wx['list']]
    wind_speed = np.round([date['wind']['speed'] for date in forecast_wx['list']])
    wind_direction = [date['wind']['deg'] for date in forecast_wx['list']]
    wind_gust = np.round([date['wind']['gust'] for date in forecast_wx['list']])
    pop = [date['pop'] for date in forecast_wx['list']]

    df = pd.DataFrame(
        data={
            'Date':dts,
            'Temperature': temperature,
            # 'Temperature Min': temp_min,
            # 'Temperature Max': temp_max,
            'Pressure': pressure,
            'Relative Humidity': humidity,
            # 'Weather': weather,
            'Weather Description': weather_description,
            # 'Clouds': clouds,
            'Wind Speed': wind_speed,
            'Wind Direction': wind_direction,
            # 'Wind Gust': wind_gust,
            'Pop': pop
            }
        )
    return df
