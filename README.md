### Baltimore City Police Mapped Arrest Locations for Weapons Incidents, 2024

This is a project mapping 2024 weapons-related incidents in the city. The data are from [https://data.baltimorecity.gov/datasets/5d378673c8f4427fb9d02de362d5b634_0/explore?location=-0.000000%2C0.000000%2C1.01](https://data.baltimorecity.gov/datasets/5d378673c8f4427fb9d02de362d5b634_0/explore?location=-0.000000%2C0.000000%2C1.01) 

`bpd_cleaning.py`  
  The primary script for cleaning the data.

`app.py`  
  The Plotly Dash dashboard application.

`BPD_Arrests.geojson`  
  Source is the OpenBaltimore website. Uploaded to GH via Release. Date updated 3/10/2025, date created 3/10/2021.
  
`/CJIS/`  
  Maryland Criminal Justice Information System codes and statute descriptions for my reference in understanding BPD arrest codes to clean and present them in a meaningful way.

`/CJIS/cjiscode.xml`  
  I merged CJIS codes into the file for more consistent charge descriptions. [https://www.mdcourts.gov/district/chargedb](https://www.mdcourts.gov/district/chargedb)  

`/CJIS/CJIS_codes.csv`  
  My cleaned version of cjiscode.xml.

`/archive/`  
  Contains older files.
  
`/archive/911_Weapons_Incident_Inner_Harbor_Locations_2024.html`  
Earlier version of a map for this project.  

`requirements.txt`  
  Requirements for the program and app.

`Procfile`  
  web: gunicorn app:server

`runtime.txt`  
  python-3.12.3
