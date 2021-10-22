import webbrowser
import pandas as pd
from shapely.geometry import Point  # Shapely for converting lat/lon to geometry
import geopandas as gpd  # To create GeodataFrame
import folium

from clean_air.visualise.assets import data

AURN_SITES = '/net/home/h05/clucas/CAF_Example_Data_Files/AURN_Observations/' \
             'AURN_Site_Information.csv'

AIRCRAFT_TRACK = '/net/home/h06/cbosley/Projects/adaq-aqi/cap-sample-data/' \
                 'aircraft/MOCCA_M251_20190903.nc'


def get_aurn__sites_site_map() -> map:
    """This function returns a site_map object with all the AURN sites plotted 
    on it.

    call display(site_map) to show this site_map in a Jupyter notebook
    There is also an html version generated for use at AURN.html '"""

    site_map = folium.Map(location=[50.72039, -1.88092], zoom_start=7)

    data_file = AURN_SITES
    df = pd.read_csv(data_file, skiprows=0, na_values=['no info', '.'])

    # Add geometry and convert to geopanda
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326",
                           geometry=gpd.points_from_xy(df.Longitude,
                                                       df.Latitude))

    # insert multiple markers, iterate through list
    # add a different color marker associated with type of volcano
    geo_df_list = [[point.xy[1][0], point.xy[0][0]] for point in gdf.geometry]

    i = 0
    for coordinates in geo_df_list:
        # assign a color marker for the type of AURN site
        if gdf.Type[i] == "URBAN_BACKGROUND":
            type_color = "green"
        elif gdf.Type[i] == "URBAN_TRAFFIC":
            type_color = "blue"
        elif gdf.Type[i] == "RURAL_BACKGROUND":
            type_color = "orange"
        else:
            type_color = "purple"

        # now place the markers with the popup labels and data
        site_map.add_child(folium.Marker(location=coordinates,
                                         popup=
                                         # "Year: " + str(gdf.Year[i]) + 
                                         # '<br>' +
                                         "Name: " + str(gdf.Name[i]) + '<br>' +
                                         "Type: " + str(gdf.Type[i]) + '<br>' + 
                                         "Coordinates: " + str(geo_df_list[i]),
                                         icon=folium.Icon(
                                             color="%s" % type_color)))
        # TODO: Remove trailing '+' from L.50 ("Type") if necessary.
        i = i + 1

    folium.LayerControl().add_to(site_map)

    site_map.save("assets/AURN.html")  # Save my completed site_map

    return site_map


def get_aircraft_track_map(aircraft_track_coords=AIRCRAFT_TRACK) -> map:
    m5 = folium.Map(location=[50.72039, -1.88092], zoom_start=8)

    # Creating feature groups
    f1 = folium.FeatureGroup("Aircraft track 1")

    # Adding lines to the different feature groups
    line_1 = folium.vector_layers.PolyLine(aircraft_track_coords,
                                           popup='<b>Path of Aircraft</b>',
                                           tooltip='Aircraft',
                                           color='blue', weight=5).add_to(f1)

    f1.add_to(m5)

    folium.LayerControl().add_to(m5)

    m5.save("assets/AircraftTrack.html")  # Save my completed map

    return m5

# get_aurn__sites_map()
# get_aircraft_track_map(data.get_coords1())
