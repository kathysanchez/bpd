### Baltimore City Police Mapped Arrest Locations for Weapons Incidents, 2025

This is a project mapping 2025 weapons-related incidents in the city. The data are from [https://data.baltimorecity.gov/datasets/619ec10c14b346f784a5a07bad4c43cd_0/explore?location=39.297493%2C-76.618650%2C11](https://data.baltimorecity.gov/datasets/619ec10c14b346f784a5a07bad4c43cd_0/explore?location=39.297493%2C-76.618650%2C11) 

`bpd_cleaning.py`  
  The primary script for cleaning the data.

`app.py`  
  The Plotly Dash dashboard application.

`BPD_Arrests.geojson`  
  Source is the OpenBaltimore website. Date updated 6/29/2026, date created 3/10/2021, updated weekly.
  
`/CJIS/`  
  Maryland Criminal Justice Information System codes and statute descriptions for my reference in understanding BPD arrest codes to clean and present them in a meaningful way.

`/CJIS/cjiscode.xml`  
  I merged CJIS codes into the file for more consistent charge descriptions. [https://www.mdcourts.gov/district/chargedb](https://www.mdcourts.gov/district/chargedb)  

`/CJIS/CJIS_codes.csv`  
  My cleaned version of cjiscode.xml.

`CJIS/CJIS_subset_descriptions_list.csv`
  This is an exported list of original Maryland crime code descriptions. I exported them here to manually clean them.
  
`CJIS/CJIS_subset_descriptions_list_edits.csv`
  This file shows original Maryland crime code descriptions and how I manually combined and simplified them into new categories. bpd_cleaning.py reads in this CSV.

`/archive/`  
  Contains older files. 

`requirements.txt`  
  Requirements for the program and app. 

`Procfile`  
  web: gunicorn app:server 

`runtime.txt`  
  python-3.14.6
