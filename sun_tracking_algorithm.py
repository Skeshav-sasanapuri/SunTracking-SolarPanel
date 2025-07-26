from pvlib.location import Location  # To get solar Altitude and Azimuth
import pandas as pd
from time import gmtime, strftime
import numpy as np

"""
This program helps track the location of the sun in the sky given the date, time, location, and altitude
It then gets the sun vector
Using this sun vector, it helps align the normal of the solar panel supported by 4 pistons to this sun vector thereby 
enabling maximum efficiency
"""

##########################################################################################
# Set input Parameters (Need to be calibrated while setting up the system on the house)
latitude = 40.7128  # Longitude and latitude of the location of the house
longitude = -74.0060
altitude = 0  # Height above sea level in meters
timezone = 'America/New_York'  # Time zone of the location of the house
# Set input Parameters (Need to be calibrated while setting up the system on the house)
panel_width = 1.0  # panel width in meters in x direction
panel_height = 2.0  # panel height in meters in y direction
max_piston_height_m = 0.3048  # 12 inches in meters
##########################################################################################


##########################################################################################
# Get current date/time from system
current_date_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

# Create a pandas dataframe named date_time with current date time and timezone
date_time = pd.Timestamp(current_date_time, tz=timezone)

# sun position code
site = Location(latitude, longitude, tz=timezone, altitude=altitude)  # Get attributes of sun for given lat/long/alt/tz
solar_position = site.get_solarposition(date_time)  # Get position of sun for given date and time
azimuth = solar_position['azimuth'].values[0]  # Angle of sun from true north in the clockwise direction on the ground
elevation = solar_position['elevation'].values[0]  # Angle from horizon to the sun

# Convert Sun azimuth and elevation to sun vector. We can do this by converting the spherical coordinated to cartesian
# coordinates
azimuth_rad = np.deg2rad(azimuth)  # Convert degrees to radians
elevation_rad = np.deg2rad(elevation)
x = np.cos(elevation_rad) * np.sin(azimuth_rad)
y = np.cos(elevation_rad) * np.cos(azimuth_rad)
z = np.sin(elevation_rad)
sun_vector = np.array([x, y, z])
##########################################################################################


##########################################################################################
# let each of the corners be A, B, C, D starting from top left, top right, bottom left, bottom right
corners = {
    'A': np.array([-panel_width / 2, -panel_height / 2]),
    'C': np.array([panel_width / 2, -panel_height / 2]),
    'TopMid': np.array([0.0, panel_height / 2]),
}
##########################################################################################


##########################################################################################
# Convert the sun position to solar panel tilt
# Solar panel has 4 adjustable linear actuators/legs. Each leg can be raised or lowered to tilt the panel
# get the plane that is normal to the sun vector
# Assuming we anchor A at 0, we get values for B, C, D

# Project the sun vector onto the panel plane directions
dz_dx = -sun_vector[0] / -sun_vector[2]  # slope in x
dz_dy = -sun_vector[1] / sun_vector[2]  # slope in y

# Assume A at height 0 and compute other heights relative to A
def height(x, y, x0, y0):
    dx = x - x0
    dy = y - y0
    return dz_dx * dx + dz_dy * dy

x0, y0 = corners['A']
heights_m = {
    'A': 0.0,
    'C': height(*corners['C'], x0, y0),
    'TopMid': height(*corners['TopMid'], x0, y0)
}

# Normalize heights to keep within piston limits
raw_vals = np.array(list(heights_m.values()))
raw_vals -= np.min(raw_vals)  # set minimum to 0
if np.max(raw_vals) > 0:
    raw_vals *= max_piston_height_m / np.max(raw_vals)
else:
    raw_vals[:] = 0  # if sun is overhead, all same height

# Convert to inches and display
heights_inches = {name: val / 0.0254 for name, val in zip(heights_m.keys(), raw_vals)}

print(f"Sun Azimuth: {azimuth:.2f}°, Elevation: {elevation:.2f}°")
print("Piston Heights (in inches):")
for name, h in heights_inches.items():
    print(f"  {name}: {h:.2f}\"")
