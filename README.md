# KMLBuilder

KMLBuilder is a module designed to ingest user-provided GPS coordinates and/or geo-located images, and to produce a final KML file with these. The end result is a folder with the final KML file (w/o coordinates) and an additional 'img' folder containing (resized or not) geo-located images to be accessed via a GIS software of preference. Cuyrrently, this works with GoogleEarth. 

Below are the input requirements for both geo-located images and GPS coordinates:
  - The Pandas DataFrame must have these headers: 'placemark', 'keep_elevation', 'time', 'lat', 'lon', 'elevation'
  - 'placemark' is the name of the placemark(s) to be chosen by the user; e.g. if there are more than one trip, then the user could name each group of coordinates individually
  - 'keep_elevation' is a binary (i.e. 1 or 0) telling the module whether to clamp coordinates to the ground or display the actual elevation recorded  
  - 'time' is not required; currently kept for future developments purposes
  - 'lat', 'lon' GPS coordinates must be in decimal WGS84 GCS
  - 'elevation' is the altitude measured in metres; please note that this needs to be provided if the user wants to display it as is in the GIS of choice
  - Image format must be one handled by PIL (Pillow) 
  - Image geo-location must be present in their EXIF 
  - Image geo-location coordinates must be in WGS84 GCS
  - Image EXIF requirements are: 'GPSInfo' for geo-location data extraction, 'DateTimeOriginal' for pictures ordering


### Requirements

KMLBuilder uses a number of open source projects to work properly:

* [io]
* [datetime]
* [pathlib]
* [zipfile]
* [xml.dom.minidom]
* [PIL]
* [pandas]
* [numpy]
* [colour]

### Installation

Install the dependencies and the module as you would normally:
```python
pip install KMLBuilder
```


Usage as follows:

```python
from GeoFun.KMLBuilder import CreateKmlFile
import pandas as pd


# 1) Load the coordinates data file into a Pandas DataFrame, 
gps_coords_raw = "coordinates/Apulia.csv"
gps_coords_df = pd.read_csv(gps_coords_raw)

# 2) the folder location of images to be loaded into the KML, and: 
img_folder = "images/"

# 3) and the file location of where the KML should be saved
kml_output = "kml/Apulia/"

# 4) and ingest everything into the CreateKmlFile() function: 
CreateKmlFile(kml_output,
              coords_df=gps_coords_df, 
              img_input_folder=img_folder, 
              resize_opt=100, # This is the resize filesize (in KB); can also be expressed as a 0-1 for percentage
              zip_files=True, # whether to zip the KML folder
              verbose=False) # whether to make the process verbose or not
```

### Todos

 - Expand module output types
 - Improve quality
 - Avoid module-sucking 
 - Any idea, fire away! :)

License
----

GNU GPLv3



 
