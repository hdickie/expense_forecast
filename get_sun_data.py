import requests
import json
import datetime
import time
import pandas as pd

f = r"https://api.sunrise-sunset.org/json?"

def sunrisesunset(f,d):
    params = {"lat": 37.7749, "lng": -122.4194, "date": d, "formatted":0}
    a = requests.get(f, params=params)
    a = json.loads(a.text)
    a = a["results"]
    sunrise = datetime.datetime.strptime(a["sunrise"],'%Y-%m-%dT%H:%M:%S+00:00')
    sunset = datetime.datetime.strptime(a["sunset"],'%Y-%m-%dT%H:%M:%S+00:00')
    sunrise = sunrise - datetime.timedelta(hours=8)
    sunset = sunset - datetime.timedelta(hours=8)
    return str(d)+','+str(sunrise.strftime('%H:%M:%S'))+','+str(sunset.strftime('%H:%M:%S'))

all_days = pd.date_range('2024-02-02','2034-02-02')
all_days = [ d.strftime('%Y-%m-%d') for d in all_days ]
for d in all_days:
    print(sunrisesunset(f,d))
    time.sleep(1)
