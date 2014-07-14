# A set of global variables (more or less) defining things that lots of
# pieces of diags use/can use.

# Coordinates from maps generated for lnd diags, obs set 3 from NCAR -
# http://www.cgd.ucar.edu/tss/clm/diagnostics/clm4cn/i1860-2009cnGCPs3-obs/set3/set3.html

all_regions = {
"Alaskan Arctic": [66, 72, -170, -140], 
"Antarctica": [-90, -65, -180, 180], 
"Canadian Arctic": [66, 90, -120, -60], 
"Greenland": [60, 90, -60, -20], 
"Polar": [60, 90, -180, 180],  
"Russian Arctic": [66, 90, 70, 170], 
"Alaska": [59, 67, -170, -140], 
"Central Canada": [50, 62, -100, -80], 
"Eastern Canada": [50, 60, -80, -55],
"Eastern Siberia": [50, 67, 90, 140], 
"Northern Europe": [60, 70, 5, 45],  
"Northwest Canada": [55, 67, -125, -100], 
"Western Siberia": [55, 67, 60, 90],  
"Central U.S.": [30, 50, -105, -90],  
"Eastern U.S.": [30, 50, -90, -70],  
"Europe": [45, 60, -10, 30],
"Mediterranean": [34, 45, -10, 30],
"Western U.S.": [30, 50, -130, -105],  
"Amazonia": [-10, 0, -70, -50],  
"Central Africa": [-5, 5, 10, 30],  
"Central America":  [5, 16, -95, -75], 
"Indonesia": [-10, 10, 90, 150],  
"Brazil":  [-24, -10, -65, -30], 
"India": [10, 24, 70, 90],  
"Indochina": [10, 24, 90, 120],  
"Sahel": [6,16,-5,15],
"Southern Africa": [-25, -5, 10, 40],  
"Arabian Peninsula": [16, 30, 35, 60], 
"Australia": [-30, -20, 110, 145],  
"Central Asia": [35, 50, 55, 70],  
"Mongolia": [40, 50, 85, 120],  
"Sahara Desert": [16, 30, -20, 30],
"Tigris Euphrates": [30, 40, 37, 50],
"Tibetan Plateau": [30, 40, 80, 100],  
"Central Asia": [40, 50, 40, 100],  
"Eastern China": [30, 40, 100, 120],  
"Mediterranean and Western Asia": [30, 45, -10, 60],
"Central and Eastern Mongolia and NE China": [40, 50, 100, 130],
"Sahara Desert and Arabian Peninsula": [15, 30, -15, 60],
"Southern Asia": [20, 30, 60, 120],  
"Tibetan Plaeau": [30, 40, 80, 100],
"N. Hemisphere Land": [0, 90, -180, 180],  
"S. Hemisphere Land": [-90, 0, -180, 180],  
"Global": [-90, 90, -180, 180],
#"User defined": [0, 0, 0, 0],
}

# Right now, this is just used for web page generation. 
#I don't know if it has utility in the currenty diags
region_categories = {
"Polar": ['Alaskan Arctic', 'Antarctica', 'Canadian Arctic', 'Greenland', 'Polar', 'Russian Arctic'],
"Boreal": ['Alaska', 'Central Canada', 'Eastern Canada', 'Eastern Siberian', 'Northern Europe', 'Northwest Canada', 'Western Siberia'],
"Middle Latitudes": ['Central U.S.', 'Eastern U.S.', 'Europe', 'Mediterranean', 'Western U.S.'],
"Tropical Rainforest": ['Amazonia', 'Central Africa', 'Central America', 'Indonesia'],
"Tropical Savanna": ['Brazil', 'India', 'Indochina', 'Sahel', 'Southern Africa'],
"Arid": ['Arabian Peninsula', 'Australia', 'Central Asia', 'Mongolia', 'Sahara Desert', 'Tigris EUphrates'],
"Highland": ['Tibetan Plateau'],
"Asia": ['Central Asia', 'Eastern China', 'Mediterranean and Western Asia', 'Central and Eastern Mongolia and NE China', 'Sahara Desert and Arabian Peninsula', 'Southern Asia', 'Tibetan Plateau'],
"Hemispheric and Global": ['Global Land', 'Northern Hemisphere Land', 'Southern Hemisphere Land']
}


all_months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
all_seasons = ['DJF', 'MAM', 'JJA', 'SON', 'ASO', 'FMA'] # The last 2 were in some obs sets

# I'd like these to move to a packages/defines.py, but the current design
# doesn't favor that
#all_packages = ['lmwg', 'amwg']
#lmwg_sets = []
#amwg_sets = []
#lmwg_set1_properties = []
# ...


