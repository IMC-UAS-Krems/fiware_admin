# Kittenberger Erlebnisgärten Data Simulation

This example implements a simulated data instance for Kittenberger Erlebnisgärten – a renowned garden and leisure attraction in Schiltern, Lower Austria. The simulation is intended for a prototyping workshop in order to explore smart service applications on environmental performance and visitor engagement.

## Overview

Kittenberger Erlebnisgärten covers over 60,000 square meters and features more than 50 themed gardens. The attraction includes interactive zones, animal encounters, seasonal events, and a garden center. In this use case we simulate sensor data for 20 different sites across the garden.

## Simulated Sensors

For each of the 20 sites, the following sensors will be simulated:

- **Temperature**: Varying according to an intra-day pattern with higher readings during daytime.
- **Light**: Reflecting ambient daylight conditions.
- **Air Quality**: Monitoring parameters such as CO2 and NOx levels.
- **Humidity**: Measuring relative humidity.
- **Soil Moisture**: Tracking water content in the soil.
- **Electricity Usage**: Simulating energy consumption at each site.

Each sensor simulation includes realistic intra-day patterns to mimic changes throughout the day and night.

## Data and Map Reference

A park plan map has been downloaded for reference and is located in the same directory as this example:

- `./kittenberger_gartenplan.pdf`

This reference can be used when working with geolocation data to accurately simulate sensor positions across the garden and define sectors as polygons for example.

## Usage

1. **Setup**: Ensure you have all required dependencies installed.
2. **Simulation Start**: Run the simulation script to generate sensor data. The script will simulate intra-day sensor trends accordingly.
3. **Visualization**: Use the provided geolocation and sensor data to build dashboards or analytics (e.g. using FIWARE and Dash).

## Additional Information

For more details about Kittenberger Erlebnisgärten, visit:

- [Official Website](https://www.kittenberger.at/)
- [Map Location](https://maps.app.goo.gl/Xr9X2JRYNY73CSzm6)
