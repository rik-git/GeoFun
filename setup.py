from setuptools import setup

setup(
  name = 'GeoFun',         # How you named your package folder (MyLib)
  packages = ['GeoFun'],   # Chose the same as "name"
  version = '0.1',      # Start with a small number and increase it with every change you make
  license='GNU GPLv3',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description='A package to process and work with geo-data',   # Give a short description about your library
  long_description=open('README.md', encoding='utf-8').read(),
  long_description_content_type='text/markdown',
  author = 'Riccardo Mogavero',                   # Type in your name
  author_email = 'riccardomogavero@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/rik-git/GeoFun',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/rik-git/GeoFun/archive/0.1.tar.gz',    # I explain this later on
  keywords = ['kml', 'geolocated images', 'GIS', 'kml builder', 'GoogleEarth', 'embed images into kml'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'datetime',
          'pathlib',
          'Pillow',
          'pandas',
          'numpy',
          'colour'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
  ],
)
