import streamlit as st
import geopandas as gpd
import os
import rasterio
import numpy as np
import PIL.Image
import folium
from streamlit_folium import st_folium
from rasterstats import zonal_stats
import datetime

app_title = 'BayByeMos Risiko - Karte'
app_sub_title = 'Created with streamlit-folium package for Python'


def display_map(tif_file, json_file, day, wdir, data_folder):
    ###################################################################################################
    ######### Raster file handling
    # Open the GeoTIFF file
    with rasterio.open(tif_file) as src:
        # Read the first band
        band = src.read(day)
        # Create doy string
        doy_string = "r_mean_band_" + str(day)
        # Get the affine transform for the raster
        bounds = src.bounds
        # Get the image bounds
        image_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]

    ###################################################################################################
    ######### Create a colormap function
    def value_to_color(value):
        if np.isnan(value):
            return (0,0,0,0) # Transparent for NoData
        elif 0.8 <= value < 1.0:
            return (224, 243, 248, 255) # White
        elif 1.0 <= value < 1.2:
            return (145, 191, 219, 255) # Blue
        elif 1.2 <= value < 1.5:
            return (254, 224, 144, 255) # Yellow
        elif value > 1.5:
            return (215, 48, 39, 255) # Red
        else:
            return (0, 0, 0, 0) # Transparent for values outside of the specified ranges 

    ###################################################################################################
    ######### Apply color map to the raster, save as png and Create Image Overlay
    colored_data = np.zeros((band.shape[0], band.shape[1], 4), dtype=np.uint8)

    for i in range(band.shape[0]):
        for j in range(band.shape[1]):
            colored_data[i, j] = value_to_color(band[i, j])

    img = PIL.Image.fromarray(colored_data)
    img_path = os.path.join(wdir, data_folder, 'colored_img.png')
    img.save(img_path)

    # Create Image Overlay
    img_overlay = folium.raster_layers.ImageOverlay(
        image=img_path,
    #    image=band,
        name="R0-Werte",
        bounds=image_bounds,
        opacity=0.6,
        #interactive=True,
        cross_origin=False,
        zindex=1
    )

    ###################################################################################################
    ######### 
    # Load GeoJson data
    kreise = gpd.read_file(json_file)

    ###################################################################################################
    ######### Create Tooltip and Folium.GeoJson Layer
    # Tooltip Creation
    tooltip = folium.GeoJsonTooltip(
        fields=["gen", "bez", "r_mean_b17"], # Statt Band zu definieren dann doy_string angeben, wenn für jeden Tag ein r_mean da ist
        aliases=["Name:", "Typ:", "Mittlerer R0-Wert"],
        localize=True,
        sticky=False,
        labels=True,
        style="background-color: #F0EFEF"
    )

    # Add the GeoJson layer with the style function
    json = folium.GeoJson(kreise,
                name= "Landkreisgrenzen",
                color="black",
                weight=1,
                fill_color="YlGn",
                fill_opacity=0,
                tooltip=tooltip)

    ###################################################################################################
    ######### Create and fill the folium map
    # Map
    m = folium.Map(location=[51.125, 10.375], 
                zoom_start=6,
                zoom_control=True,
                scrollWheelZoom = False,
                tiles='CartoDB positron',
                #dragging = False
                )

    # Add Raster Image
    m.add_child(img_overlay)

    # Add Shapefiles / Choropleth
    m.add_child(json)

    # Add Layer Control
    #folium.LayerControl().add_to(m)

    #st.write(json.head())
    #st.write(json.columns)
    st_map = st_folium(m, width= 700, height=650)
    
    return st_map

def select_file(year):
    wdir = os.getcwd()
    data_folder = 'data'
    tif_folder = 'geotif'
    tif_filename = 'WNV' + str(year) + '.tif'
    return os.path.join(wdir, data_folder, tif_folder, tif_filename)

def main():
    st.set_page_config(app_title)
    st.title(app_title)
    st.caption(app_sub_title)

    # Set path variables
    wdir = os.getcwd()
    data_folder = 'data'
    #tif_folder = 'geotif'
    #tif_filename = 'WNV2022.tif'
    #tif_path = os.path.join(wdir, data_folder, tif_folder, tif_filename)
    json_filename = 'kreise_germany_simplified_500.geojson' # 'kreise_germany_simplified_100.geojson'
    json_path = os.path.join(wdir, data_folder, json_filename)

    # Define DOY variable
    doy = 200

    # Get lastclicked coordinates
    #st.write(st_map['last_clicked']['lat'])
    #st.write(st_map['last_clicked']['lng'])

    # Date Input
    today = datetime.datetime.now()
    last_week = today - datetime.timedelta(days=7)
    d1 = st.sidebar.date_input("Select Date", value=today, min_value=datetime.date(2017, 1, 1), max_value = today)
    d_range = st.sidebar.date_input("Select Date range to display R0 values", (last_week, today), min_value=datetime.date(2017, 1, 1), max_value = today)
    # Get Year from d1
    year = d1.timetuple().tm_year
    # Get DOY from d1
    doy = d1.timetuple().tm_yday

    # Path variables
    tif_path = select_file(year)

    # Display Map
    map = display_map(tif_path, json_path, doy, wdir, data_folder)
    
    #st.write(map)
    
    # Print Map
    #st.write(map)

    # Display Metrics


    

if __name__ == "__main__":
    main()