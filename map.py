import requests
import json
from skyfield.api import EarthSatellite
from skyfield.api import load, wgs84
from datetime import datetime, timedelta
from pytz import timezone
import folium
import itertools
import webbrowser

homelat = 45.1
homelon = -75.3

noradid = '25544' # NORAD identifier - '25544' for international space station

tle = 'https://db.satnogs.org/api/tle/'
tz = timezone('UTC')
now = datetime.now(tz)
ts = load.timescale()
t = ts.utc(now, tz)
sats = []
start = ts.utc(now.year, now.month, now.day, now.hour, now.minute)
delta = now + timedelta(days=1)
end = ts.utc(delta.year, delta.month, delta.day, delta.hour, delta.minute)
home = wgs84.latlon(homelat, homelon)
map = folium.Map(location=[homelat,homelon], tiles='OpenStreetMap', zoom_start=2, mercator_project=True)
folium.Marker(location=(homelat, homelon), tooltip='Home').add_to(map)

def interval_generator():
  from_date = datetime.now(tz)
  while True:
    yield from_date
    from_date = from_date - timedelta(minutes=5)

r = requests.get(tle)
sats = json.loads(r.content.decode())
id = int(noradid)
for sat in sats:
    if sat['norad_cat_id'] == id:
        # print(sat['tle0']) # satellite name
        # print(sat['tle1']) # TLE line 1
        # print(sat['tle2']) # TLE line 2
        satellite = EarthSatellite(sat['tle1'], sat['tle2'], sat['tle0'], ts)
        days = t - satellite.epoch
        # print(f"{sat['tle0']} Epoch: {satellite.epoch.utc_strftime('%Y %b %d %H:%M:%S')} " + "{:.3f} days from Epoch\n".format(days))
        geocentric = satellite.at(t)
        latlon = wgs84.geographic_position_of(geocentric)
        # folium.Marker(location=(latlon.latitude.degrees,latlon.longitude.degrees), tooltip=f"{sat['tle0']}").add_to(map)
        points = itertools.islice(interval_generator(), 12)
        track = []
        for point in sorted(points, reverse=True):
            newts = load.timescale()
            newtime = newts.utc(point, tz)
            geocentric = satellite.at(newtime)
            latlon = wgs84.geographic_position_of(geocentric)
            track.append((latlon.latitude.degrees,latlon.longitude.degrees))
            folium.Marker(location=(latlon.latitude.degrees,latlon.longitude.degrees), tooltip=f"{sat['tle0']} \n {point}").add_to(map)
        folium.PolyLine(sorted(track, reverse=True), tooltip=sat['tle0']).add_to(map)
        map.save('map.html')
        webbrowser.open('map.html')

        print(f"{t.utc_strftime('%Y %b %d %H:%M:%S')} - Current location: {latlon.latitude.degrees}, {latlon.longitude.degrees}, alt: {latlon.elevation.km}km\n")
        # t, events = satellite.find_events(home, start, end, altitude_degrees=1.0)
        # for ti, event in zip(t, events):
        #     name = ('aos', 'max elevation', 'los\n')[event]
        #     print(ti.utc_strftime('%Y %b %d %H:%M:%S'), name)
