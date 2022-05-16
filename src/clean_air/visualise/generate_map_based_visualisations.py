import webbrowser
import pandas as pd
import geopandas as gpd  # To create GeodataFrame
import folium
import branca.colormap as cm
import os

from clean_air.util import file_converter as fc

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

def get_aurn_sites_site_map(site_data, output_path) -> map:
    """This function returns a site_map object with all the AURN sites plotted 
    on it.

    call display(site_map) to show this site_map in a Jupyter notebook
    There is also an html version generated for use at AURN.html '"""

    site_map = folium.Map(location=[50.72039, -1.88092], zoom_start=7)

    data_file = site_data
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
                                         "Name: " + str(gdf.Name[i]) + '<br>' +
                                         "Type: " + str(gdf.Type[i]) + '<br>' +
                                         "Coordinates: " + str(geo_df_list[i]),
                                         icon=folium.Icon(
                                             color="%s" % type_color)))
        i = i + 1

    folium.LayerControl().add_to(site_map)

    site_map.save(output_path)  # Save my completed site_map

    return site_map


def get_aircraft_track_map(aircraft_track_coords, output_path) -> map:
    """
    Create a standard base map, read and convert aircraft track files
    into lat/lon pairs, then plot these locations on the map and draw lines
    between them (and colour them by altitude?).
    """
    # Create base map
    m5 = folium.Map(location=[50.72039, -1.88092], zoom_start=8)
    # Creating feature groups
    f1 = folium.FeatureGroup("Aircraft track 1")

    # Extract lat-lon pairs from input file (after checking valid filetype):
    filetype = os.path.splitext(aircraft_track_coords)[1]
    if filetype == '.nc':
        tmp_aircraft_df = fc.generate_dataframe(aircraft_track_coords)
        lats = tmp_aircraft_df['Latitude']
        lons = tmp_aircraft_df['Longitude']
        tmp_aircraft_track = pd.concat([lats, lons], axis=1)
        altitudes = tmp_aircraft_df['Altitude'][:-1]
        cmap = cm.LinearColormap(['blue', 'red'], vmin=100, vmax=800)
        colour_line = folium.features.ColorLine(positions=tmp_aircraft_track,
                                                colors=altitudes,
                                                colormap=cmap,
                                                nb_steps=50,
                                                weight=5)
        colour_line.add_to(f1)
    else:
        raise ValueError("Aircraft track filetype not recognised.  Please "
                         "ensure this is netCDF (i.e. '.nc').")

    f1.add_to(m5)
    folium.LayerControl().add_to(m5)

    # Save my completed map
    m5.save(output_path)

    return m5

def get_boundaries(boundary_data, output_path) -> map:
    """This function returns a site_map object with a layer displaying boundaries.

    call display(site_map) to show this site_map in a Jupyter notebook
    There is also an html version generated for use at boundaries.html '"""

    # Create base map
    boundary_map = folium.Map(location=[50.72039, -1.88092], zoom_start=7)

    # Add boundary layer
    folium.GeoJson(boundary_data).add_to(boundary_map)

    # Save my completed map
    boundary_map.save(output_path)

    return boundary_map