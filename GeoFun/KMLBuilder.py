import os
import shutil
import io
import datetime
from pathlib import Path
import zipfile

import xml.dom.minidom

from PIL import Image
import PIL.ExifTags

import pandas as pd
import numpy as np

from colour import Color

# import random



##############################################################################
### Coordinates functions

### Creates a palette of colours given two extremes and the number of labels to be coloured
"""
Input:
- no_of_colours: The number of colours required
- extreme_col_1="red": the extreme 1 colour
- extreme_col_2="blue": the extreme 2 colour
Output:
- A list of HEX-8 digits colours
"""
def ColourPicker(no_of_colours, extreme_col_1="red", extreme_col_2="blue"):
	ext_col_1 = Color(extreme_col_1)
	ext_col_2 = Color(extreme_col_2)
	
	colours_list = list(ext_col_1.range_to(ext_col_2, no_of_colours))

	final_colours = []
	for each_col in colours_list:
		hex_6char = each_col.hex_l

		col_hex_str = "99"+str(hex_6char)[1:]

		final_colours.append(col_hex_str)

	return final_colours



### Archives files and folders
"""
Input:
- zip_path: The folder name of the KML output
- zip_file_name: The file name of the ZIP
Output:
- A ZIP folder with the output, outside of the main directory to be zipped
"""
def ZipArchive(zip_path, zip_file_name):
	# Prepare paths
	length_subdir = len(zip_file_name)+1
	zip_path_file = zip_path[:-length_subdir]
	zip_file = zip_path_file+zip_file_name+".zip"

	# Create zip file
	zipf = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)

	# Archive data
	for root, dirs, files in os.walk(zip_path):
		for file in files:
			file_to_archive = os.path.join(root, file)
			zipf.write(file_to_archive, file_to_archive[len(zip_path_file):] if file_to_archive.startswith(zip_path_file) else file_to_archive)

	zipf.close()



### Get coordinates and parse data into groups:
"""
Input:
- df: the CSV
Output:
- The text string containing the coordinates to be saved into  
"""
def CoordinatesParser(df):
	## Creates list of unique placemarks from first column of dataframe
	uq_placemarks = df[['placemark', 'keep_elevation']].drop_duplicates(keep='first', inplace=False).values.tolist()

	## Loop through them, isolate data from df and create KML-ready text
	for placemark in uq_placemarks:
		placemark_name = placemark[0]
		placemark_keep_elevation = placemark[1]

		df_ = df.loc[df['placemark']==placemark_name]

		# Keep elevation if required, otherwise discard
		if placemark_keep_elevation == 1:
			df_1 = "            "+df_['lon'].map(str)+","+df_['lat'].map(str)+","+df_['elevation'].map(str)
		else:
			df_1 = "            "+df_['lon'].map(str)+","+df_['lat'].map(str)

		placemark_coords_str = df_1.str.cat(sep='\n')

		placemark.append('\n'+placemark_coords_str+'\n')


	return uq_placemarks



### Creates placemark(s) for GPS coordinates
"""
Input:
- gps_coords_df: the dataframe with GPS coordinates
- kml_doc: the KML doc
Output:
- Same KML doc inputted, with appended placemark 
""" 
def CreatePlacemark(gps_coords_df, kml_doc):
	placemarks_list = CoordinatesParser(gps_coords_df)
	placemark_no = len(placemarks_list)

	# color_palette = ['96ceb4dd','ffeeaddd','ffcc5cdd','ff6f69dd','6b5b95dd','feb236dd','d64161dd','ff7b25dd','3e4444dd','82b74bdd','405d27dd','c1946add', '7F8080dd', '7F0000FF', '7F8080dd', '7FFFAAdd']
	# selected_palette = random.choices(color_palette, k=placemark_no)

	selected_palette = ColourPicker(placemark_no)#, extreme_col_1="red", extreme_col_2="blue")


	## For each trip/placemark, add KML doc requirements, assigning a different colour for each 
	col_ix = 0
	for each_placemark in placemarks_list:
		placemark_name = each_placemark[0]
		placemark_is_flight = each_placemark[1]
		placemark_coords = each_placemark[2]

		if placemark_is_flight == 0:
			alt_mode = 'clampToGround'
			line_width = 2
		else:
			alt_mode = 'absolute'
			line_width = 1

		col_pick = selected_palette[col_ix]
		col_ix += 1


		pl = kml_doc.createElement('Placemark')

		name = kml_doc.createElement('name')
		name.appendChild(kml_doc.createTextNode(placemark_name))
		
		LineString = kml_doc.createElement('LineString')
		extrude = kml_doc.createElement('extrude')
		extrude.appendChild(kml_doc.createTextNode('1'))
		altitudeMode = kml_doc.createElement('altitudeMode')
		altitudeMode.appendChild(kml_doc.createTextNode(alt_mode))
		coordinates = kml_doc.createElement('coordinates')
		coordinates.appendChild(kml_doc.createTextNode(placemark_coords))
		LineString.appendChild(extrude)
		LineString.appendChild(altitudeMode)
		LineString.appendChild(coordinates)

		Style = kml_doc.createElement('Style')
		LineStyle = kml_doc.createElement('LineStyle')
		color = kml_doc.createElement('color')
		color.appendChild(kml_doc.createTextNode(col_pick))
		width = kml_doc.createElement('width')
		width.appendChild(kml_doc.createTextNode(str(line_width)))
		LineStyle.appendChild(color)
		LineStyle.appendChild(width)
		Style.appendChild(LineStyle)

		pl.appendChild(name)
		pl.appendChild(LineString)
		pl.appendChild(Style)

		document = kml_doc.getElementsByTagName('Document')[-1]
		document.appendChild(pl)



##############################################################################
### Images 

### Iterates through image files
"""
Input:
- folder='input/images/': The folder where images to be processed are saved 
Output:
- The filenames, ordered by picture taken date
"""
def FilesIterator(folder='input/images/'):
	entries = Path(folder)

	valid_files = []
	for entry in entries.iterdir():
		if entry.is_file():
			try:
				img = Image.open(entry)
				data = GetHeaders(img)
				date_original = data['DateTimeOriginal']

				date_original = datetime.datetime.strptime(date_original, "%Y:%m:%d %H:%M:%S")
			except:
				date_original = None

			valid_files.append([folder+entry.name, date_original])

	valid_files.sort(key=lambda x: x[1])
	valid_files_ordered = []
	for each_file in valid_files:
		valid_files_ordered.append(each_file[0])

	return valid_files_ordered



### Function used to determine sides of newly resized image, given a new area and original sides measures
"""
Input:
- chosen_A: The new, chosen area
- given_w: the original width
- given_h: the original height
Output:
- The new width and height of the resized image
"""
def FindSides(chosen_A, given_w, given_h):
	given_R = float(given_w) / float(given_h)		# Find W/H ratio
	new_h = (chosen_A / given_R)**(1/2.0)
	new_w = new_h * given_R
	
	new_h = int(round(new_h, 0))
	new_w = int(round(new_w, 0))
	
	result_find_sides = (new_w,new_h)
	
	return result_find_sides



### Handles the opening of an individual file.
"""
Input:
- file_name: the name of the file to get
- destination_folder: the folder where images (resized or otherwise) are saved
- resize_opt=1.0: the image resizing option; if less than 1, it'd percentage resizing, otherwise in KILOBYTES 
Returns:
A file
"""
def GetFile(file_name, destination_folder, resize_opt=1.0, resize_tolerance=5):

	new_img = None

	try:
		img = img_orig = Image.open(file_name)
		exif = img.info['exif']

		img_size_KB = (os.stat(file_name).st_size) / 1024
		filename = os.path.basename(file_name)

		original_w, original_h = img.size
		original_area = original_w * original_h

		filename_destination = destination_folder+filename

		if resize_opt >= 0.01 and resize_opt <= 1.0:
			resize_ratio = resize_opt

			new_area = original_area * resize_ratio
			new_w, new_h = FindSides(new_area, original_w, original_h)

			new_img = img.resize((new_w,new_h), Image.ANTIALIAS)

			new_img.save(filename_destination, exif=exif)
			new_img = Image.open(filename_destination)

		elif resize_opt > 50.0 and resize_opt <= img_size_KB:
			aspect = img.size[0] / img.size[1]

			while True:
				with io.BytesIO() as buffer:
					img.save(buffer, format="JPEG", exif=exif)
					data = buffer.getvalue()
				filesize = len(data)    
				size_deviation = filesize / (resize_opt*1024)

				if size_deviation <= (100 + resize_tolerance) / 100:
					# filesize fits
					with open(filename_destination, "wb") as f:
						f.write(data)
					new_img = Image.open(filename_destination)
					break
				
				else:
					# filesize not good enough => adapt width and height; use sqrt of deviation since applied both in width and height
					new_width = img.size[0] / size_deviation**0.5    
					new_height = new_width / aspect
					# resize from img_orig to not lose quality
					img = img_orig.resize((int(new_width), int(new_height)))

		else:
			new_img = img
			print("File resizing ignored: the file resize chosen is either below the 50KB or 1% thresholds, or larger than the original size. Please chose a different figure for 'resize_opt'.")

	except:
		new_img = None

	return new_img



### Reads the headers from the file.
"""Handles getting the EXIF headers and returns them as a dict.
Input:
- the_file: A PIL file object
Output:
- A dict mapping keys corresponding to the EXIF headers of a file.
"""
def GetHeaders(the_file):#file_name):
	try:
		data = {
			PIL.ExifTags.TAGS[k]: v
			for k, v in the_file._getexif().items()
			if k in PIL.ExifTags.TAGS
		}			

	except IOError:
		print("No file found.")
		data = None
	
	return data



### Converts EXIF GPS headers data to a decimal degree.
"""Converts the Degree/Minute/Second formatted GPS data to decimal degrees.
Input:
- degree_num: The numerator of the degree object.
- degree_den: The denominator of the degree object.
- minute_num: The numerator of the minute object.
- minute_den: The denominator of the minute object.
- second_num: The numerator of the second object.
- second_den: The denominator of the second object.
Output:
- A deciminal degree.
"""
def DmsToDecimal(degree_num, degree_den, minute_num, minute_den, second_num, second_den):

	degree = float(degree_num)/float(degree_den)
	minute = float(minute_num)/float(minute_den)/60
	second = float(second_num)/float(second_den)/3600

	return degree + minute + second



### Parses out the the GPS headers from the headers data.
"""Parses out the GPS coordinates from the file.
Input:
- data: A dict object representing the EXIF headers of the photo.
Returns:
- A tuple representing the latitude, longitude, and altitude of the photo.
"""
def GetGps(data):

	latitude = None
	try:
		lat_dms = data['GPSInfo'][2]
		lat_ref = data['GPSInfo'][1]

		latitude = DmsToDecimal(lat_dms[0][0], lat_dms[0][1], lat_dms[1][0], lat_dms[1][1], lat_dms[2][0], lat_dms[2][1])

		if lat_ref == 'S': 
			latitude *= -1
	except:
		pass

	longitude = None
	try:
		long_dms = data['GPSInfo'][4]
		long_ref = data['GPSInfo'][3]

		longitude = DmsToDecimal(long_dms[0][0], long_dms[0][1], long_dms[1][0], long_dms[1][1], long_dms[2][0], long_dms[2][1])

		if long_ref == 'W': 
			longitude *= -1

	except:
		pass

	altitude = None
	try:
		alt_cm = data['GPSInfo'][6][0]
		alt_ref = data['GPSInfo'][6][1]

		altitude = alt_cm/alt_ref

	except:
		altitude = 0

	if latitude == None or longitude == None:
		latitude, longitude, altitude = None, None, None
	
	return latitude, longitude, altitude



### Creates an individual PhotoOverlay XML element object.
"""Creates a PhotoOverlay element in the kml_doc element.
Input:
- kml_doc: An XML document object.
- file_name: The name of the file.
- the_file: The file object.
- file_iterator: The file iterator, used to create the id.
Input:
- An XML element representing the PhotoOverlay.
"""
def CreatePhotoOverlay(kml_doc, file_name, the_file, file_iterator):
	file_basename = os.path.basename(file_name)
	file_name_clean, file_extension = os.path.splitext(file_basename)
	correct_file_name = "img/"+file_basename

	photo_id = 'photo%s' % file_iterator
	data = GetHeaders(the_file)
	coords = GetGps(data)

	po = kml_doc.createElement('PhotoOverlay')
	po.setAttribute('id', photo_id)
	name = kml_doc.createElement('name')
	name.appendChild(kml_doc.createTextNode(file_name_clean))
	description = kml_doc.createElement('description')
	description.appendChild(kml_doc.createCDATASection('<a href="#%s">'
													 'Click here to fly into '
													 'photo</a>' % photo_id))
	po.appendChild(name)
	po.appendChild(description)
	icon = kml_doc.createElement('Icon')
	href = kml_doc.createElement('href')
	href.appendChild(kml_doc.createTextNode(correct_file_name))
	camera = kml_doc.createElement('Camera')
	longitude = kml_doc.createElement('longitude')
	latitude = kml_doc.createElement('latitude')
	altitude = kml_doc.createElement('altitude')
	tilt = kml_doc.createElement('tilt')
	
	# Determines the proportions of the image and uses them to set FOV.
	try:
		width = float(data['ExifImageWidth'])
	except:
		width = float(data['ImageWidth'])

	try:
		length = float(data['ExifImageHeight'])
	except:
		length = float(data['ImageLength'])

	lf = str(width/length * -20.0)
	rf = str(width/length * 20.0)
	
	longitude.appendChild(kml_doc.createTextNode(str(coords[1])))
	latitude.appendChild(kml_doc.createTextNode(str(coords[0])))
	altitude.appendChild(kml_doc.createTextNode('30'))
	tilt.appendChild(kml_doc.createTextNode('0'))
	camera.appendChild(longitude)
	camera.appendChild(latitude)
	camera.appendChild(altitude)
	camera.appendChild(tilt)
	icon.appendChild(href)
	viewvolume = kml_doc.createElement('ViewVolume')
	leftfov = kml_doc.createElement('leftFov')
	rightfov = kml_doc.createElement('rightFov')
	bottomfov = kml_doc.createElement('bottomFov')
	topfov = kml_doc.createElement('topFov')
	near = kml_doc.createElement('near')
	leftfov.appendChild(kml_doc.createTextNode(lf))
	rightfov.appendChild(kml_doc.createTextNode(rf))
	bottomfov.appendChild(kml_doc.createTextNode('-20'))
	topfov.appendChild(kml_doc.createTextNode('20'))
	near.appendChild(kml_doc.createTextNode('10'))
	viewvolume.appendChild(leftfov)
	viewvolume.appendChild(rightfov)
	viewvolume.appendChild(bottomfov)
	viewvolume.appendChild(topfov)
	viewvolume.appendChild(near)
	po.appendChild(camera)
	po.appendChild(icon)
	po.appendChild(viewvolume)
	point = kml_doc.createElement('point')
	coordinates = kml_doc.createElement('coordinates')
	coordinates.appendChild(kml_doc.createTextNode('%s,%s,%s' %(coords[1], coords[0], coords[2])))
	point.appendChild(coordinates)
	po.appendChild(point)

	document = kml_doc.getElementsByTagName('Document')[-1]
	document.appendChild(po)



##############################################################################
### WRAPPERS

### Create final KML file:
"""Creates the KML Document with the PhotoOverlays, and writes it to a file.
Input:
- new_file_name: A string of the name of the new file to be created.
Output:
- A KML doc
"""
def CreateKmlDoc(new_file_name):
	kml_doc = xml.dom.minidom.Document()
	kml_element = kml_doc.createElementNS('http://www.opengis.net/kml/2.2', 'kml')
	kml_element.setAttribute('xmlns', 'http://www.opengis.net/kml/2.2')
	kml_element = kml_doc.appendChild(kml_element)
	document = kml_doc.createElement('Document')

	name = kml_doc.createElement('name')
	name.appendChild(kml_doc.createTextNode(new_file_name))
	document.appendChild(name)

	kml_element.appendChild(document)

	return kml_doc



### Creates KML sub document, one for each images and coordinates (linestrings), if needed
"""
Input:
- kml_doc: the KML object
- media_type=["Pictures", "Trips"]: whether images or coordinates
Output:
- Same KML doc but with a sub-'document' appended to it
"""
def CreateSubDocument(kml_doc, media_type):
	document = kml_doc.createElement('Document')

	name = kml_doc.createElement('name')
	name.appendChild(kml_doc.createTextNode(media_type))
	document.appendChild(name)

	main_document = kml_doc.getElementsByTagName('Document')[0]
	main_document.appendChild(document)



### Create final KML file
"""
Input:
- output_folder: the folder (and filename) of the KML output
- coords_df: the file location where coordinates are saved (with ['placemark', 'keep_elevation', 'time', 'lat', 'lon', 'elevation'] as headers)
- img_input_folder: the folder where geo-located images are saved
- resize_opt=1.0: the resizing of images;	- if 0.01=<resize_opt<1.0, the image will be resized as per the % chosen according to the area, 
											- if 50=<resize_opt=<original size in KB, the image will be resized as per the filesize chosen
											- anything else will be ignored
- zip_files=False: Whether to archive the output folder and its contents
- verbose=False: whether to make process verbose
Output:
- The final KML file and folder
"""
def CreateKmlFile(output_folder, coords_df=None, img_input_folder=None, resize_opt=1.0, zip_files=False, verbose=False):
	### Check that there are not existing folders with same name
	if output_folder[-1] != "/":
		out_folder = output_folder+"/"
	else:
		out_folder = output_folder

	try:
		new_file_name = os.path.basename(os.path.normpath(output_folder))
	except:
		new_file_name = output_folder
		pass

	folder_exists = os.path.exists(out_folder)
	if folder_exists:
		remove_existing = input("\nThe '"+out_folder+"' folder already exists!"+"\n"+"--> Do you want to remove all existing files/folders from it?"+"\n   (Please enter yes, y or 1, anything else for no)"+"\n   ")
		print("\n")


	try:
		### ...otherwise ask whether to delete previous files:
		if folder_exists == True and str(remove_existing).lower() not in ('y', 'yes', '1'):
			### If user doesn't want to overwrite, kill process.
			print("The process will now stop. Please move or rename the existing folder.")

		else:
			if folder_exists == True and str(remove_existing).lower() in ('y', 'yes', '1'):
				for f in os.listdir(out_folder):
					f_path = os.path.join(out_folder, f)

					try:
						if os.path.isfile(f_path):
							os.unlink(f_path)
						elif os.path.isdir(f_path): 
							shutil.rmtree(f_path)
					
					except Exception as e:
						print(e)

			### START KML PRODUCTION PROCESS:
			if img_input_folder == None and isinstance(coords_df, pd.DataFrame) != True: # Skip KML file creation if inputs not provided
				print("\nNo input file(s) was provided: exiting now.")
				pass

			elif img_input_folder == None and isinstance(coords_df, pd.DataFrame) == True: ## Skip images embedding if not required:
				try:
					os.makedirs(out_folder)
				except:
					pass

				kml_doc = CreateKmlDoc(new_file_name)
				CreatePlacemark(coords_df, kml_doc)

				kml_file_name = out_folder+new_file_name+".kml"

				kml_file = open(kml_file_name, 'wb')
				kml_file.write(kml_doc.toprettyxml('  ', newl='\n', encoding='utf-8'))

				if verbose:
					print("\nThe KML file has been created.")

			elif isinstance(coords_df, pd.DataFrame) != True: # Skip coordinates embedding if these have not been provided
				out_folder_img = out_folder+"img/"

				try:
					os.makedirs(out_folder_img)
				except:
					pass
				
				file_names = FilesIterator(img_input_folder)

				files = {}
				
				file_counter = 0
				tot_files = len(file_names)
				for file_name in file_names:
					the_file = GetFile(file_name, out_folder_img, resize_opt)
					if the_file is None:
						print("'%s' is unreadable\n" % file_name)
						file_names.remove(file_name)
						continue
					else:
						files[file_name] = the_file
					
					kml_doc = CreateKmlDoc(new_file_name)
					file_iterator = 0
					for key in files.keys():
						filename = os.path.basename(key)
						complete_file_name = out_folder_img+filename
						CreatePhotoOverlay(kml_doc, complete_file_name, files[key], file_iterator)
						file_iterator += 1


					kml_file_name = out_folder+new_file_name+".kml"

					kml_file = open(kml_file_name, 'wb')
					kml_file.write(kml_doc.toprettyxml('  ', newl='\n', encoding='utf-8'))

					if verbose:
						print("Image "+str(file_counter+1)+" out of "+str(tot_files)+" added to KML file: "+filename)
					file_counter += 1

				if verbose:
					print("\nThe images have been loaded into the KML file.")
			
			else: # Embed both images and coordinates
				out_folder_img = out_folder+"img/"

				try:
					os.makedirs(out_folder_img)
				except:
					pass
				
				file_names = FilesIterator(img_input_folder)

				files = {}
					
				file_counter = 0
				tot_files = len(file_names)
				for file_name in file_names:
					the_file = GetFile(file_name, out_folder_img, resize_opt)
					if the_file is None:
						print("'%s' is unreadable\n" % file_name)
						file_names.remove(file_name)
						continue
					else:
						files[file_name] = the_file
					
					kml_doc = CreateKmlDoc(new_file_name)
					CreateSubDocument(kml_doc, "Pictures")
					file_iterator = 0
					for key in files.keys():
						filename = os.path.basename(key)
						complete_file_name = out_folder_img+filename
						CreatePhotoOverlay(kml_doc, complete_file_name, files[key], file_iterator)
						file_iterator += 1

					CreateSubDocument(kml_doc, "Trips")
					CreatePlacemark(coords_df, kml_doc)

					kml_file_name = out_folder+new_file_name+".kml"

					kml_file = open(kml_file_name, 'wb')
					kml_file.write(kml_doc.toprettyxml('  ', newl='\n', encoding='utf-8'))

					if verbose:
						print("Image "+str(file_counter+1)+" out of "+str(tot_files)+" added to KML file: "+filename)
						file_counter += 1

				if verbose:
					print("\nBoth images and coordinates have been loaded into the KML file.")

			## Archive data, if required
			if zip_files == True:
				ZipArchive(out_folder, new_file_name)
	except:
		print("Something unexpected happened: please check your inputs (e.g. correctly geolocated images and proper coordinates dataframe.)")



