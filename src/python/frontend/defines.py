# A set of global variables (more or less) defining things that lots of
# pieces of diags use/can use.

# Coordinates from maps generated for lnd diags, obs set 3 from NCAR -
# http://www.cgd.ucar.edu/tss/clm/diagnostics/clm4cn/i1860-2009cnGCPs3-obs/set3/set3.html

from metrics.computation.region import *

all_regions = {}
all_regions['Alaskan_Arctic'] = rectregion('Alaskan_Arctic', [66, 72, -170, -140], filekey='Alaskan_Arctic')
all_regions['Antarctica'] = rectregion('Antarctica',  [-90, -65, -180, 180], filekey='Antarctica')
all_regions['Canadian_Arctic'] = rectregion('Canadian_Arctic',  [66, 90, -120, -60], filekey='Canadian_Arctic')
all_regions['Greenland'] = rectregion('Greenland',  [60, 90, -60, -20], filekey='Greenland')
all_regions['Polar'] = rectregion('Polar',  [60, 90, -180, 180],  filekey='Polar')
all_regions['Russian_Arctic'] = rectregion('Russian_Arctic',  [66, 90, 70, 170], filekey='Russian_Arctic')
all_regions['Alaska'] = rectregion('Alaska',  [59, 67, -170, -140], filekey='Alaska')
all_regions['Central_Canada'] = rectregion('Central_Canada',  [50, 62, -100, -80], filekey='Central_Canada')
all_regions['Eastern_Canada'] = rectregion('Eastern_Canada',  [50, 60, -80, -55],filekey='Eastern_Canada')
all_regions['Eastern_Siberia'] = rectregion('Eastern_Siberia',  [50, 67, 90, 140], filekey='Eastern_Siberia')
all_regions['Northern_Europe'] = rectregion('Northern_Europe',  [60, 70, 5, 45],  filekey='Northern_Europe')
all_regions['Northwest_Canada'] = rectregion('Northwest_Canada',  [55, 67, -125, -100], filekey='Northwest_Canada')
all_regions['Western_Siberia'] = rectregion('Western_Siberia',  [55, 67, 60, 90],  filekey='Western_Siberia')
all_regions['Central_U.S.'] = rectregion('Central_U.S.',  [30, 50, -105, -90],  filekey='Central_US')
all_regions['Eastern_U.S.'] = rectregion('Eastern_U.S.',  [30, 50, -90, -70],  filekey='Eastern_US')
all_regions['Europe'] = rectregion('Europe',  [45, 60, -10, 30],filekey='Europe')
all_regions['Mediterranean'] = rectregion('Mediterranean',  [34, 45, -10, 30],filekey='Mediterranean')
all_regions['Western_U.S.'] = rectregion('Western_U.S.',  [30, 50, -130, -105],  filekey='Western_US')
all_regions['Amazonia'] = rectregion('Amazonia',  [-10, 0, -70, -50],  filekey='Amazonia')
all_regions['Central_Africa'] = rectregion('Central_Africa',  [-5, 5, 10, 30],  filekey='Central_Africa')
all_regions['Central_America'] = rectregion('Central_America',   [5, 16, -95, -75], filekey='Central_America')
all_regions['Indonesia'] = rectregion('Indonesia',  [-10, 10, 90, 150],  filekey='Indonesia')
all_regions['Brazil'] = rectregion('Brazil',   [-24, -10, -65, -30], filekey='Brazil')
all_regions['India'] = rectregion('India',  [10, 24, 70, 90],  filekey='India')
all_regions['Indochina'] = rectregion('Indochina',  [10, 24, 90, 120],  filekey='Indochina')
all_regions['Sahel'] = rectregion('Sahel',  [6,16,-5,15],filekey='Sahel')
all_regions['Southern_Africa'] = rectregion('Southern_Africa',  [-25, -5, 10, 40],  filekey='Southern_Africa')
all_regions['Arabian_Peninsula'] = rectregion('Arabian_Peninsula',  [16, 30, 35, 60], filekey='Arabian_Peninsula')
all_regions['Australia'] = rectregion('Australia',  [-30, -20, 110, 145],  filekey='Australia')
all_regions['Central_Asia'] = rectregion('Central_Asia',  [35, 50, 55, 70],  filekey='Central_Asia')
all_regions['Mongolia'] = rectregion('Mongolia',  [40, 50, 85, 120],  filekey='Mongolia')
all_regions['Sahara_Desert'] = rectregion('Sahara_Desert',  [16, 30, -20, 30],filekey='Sahara_Desert')
all_regions['Tigris_Euphrates'] = rectregion('Tigris_Euphrates',  [30, 40, 37, 50],filekey='Tigris_Euphrates')
all_regions['Tibetan_Plateau'] = rectregion('Tibetan_Plateau',  [30, 40, 80, 100],  filekey='Tibetan_Plateau')
all_regions['Central_Asia'] = rectregion('Central_Asia',  [40, 50, 40, 100],  filekey='Asia')
all_regions['Eastern_China'] = rectregion('Eastern_China',  [30, 40, 100, 120],  filekey='Eastern_China')
all_regions['Mediterranean_and_Western_Asia'] = rectregion('Mediterranean_and_Western_Asia',  [30, 45, -10, 60],filekey='Med_MidEast')
all_regions['Central_and_Eastern_Mongolia_and_NE_China'] = rectregion('Central_and_Eastern_Mongolia_and_NE_China',  [40, 50, 100, 130],filekey='Mongolia_China')
all_regions['Sahara_Desert_and_Arabian_Peninsula'] = rectregion('Sahara_Desert_and_Arabian_Peninsula',  [15, 30, -15, 60],filekey='NAfrica_Arabia')
all_regions['Southern_Asia'] = rectregion('Southern_Asia',  [20, 30, 60, 120],  filekey='Southern_Asia')
all_regions['Tibetan_Plaeau'] = rectregion('Tibetan_Plaeau',  [30, 40, 80, 100],filekey='Tibet')
all_regions['N_Hemisphere_Land'] = rectregion('N_Hemisphere_Land',  [0, 90, -180, 180],  filekey='N_H_Land')
all_regions['S_Hemisphere_Land'] = rectregion('S_Hemisphere_Land',  [-90, 0, -180, 180],  filekey='S_H_Land')
all_regions['Global'] = rectregion('Global',  [-90, 90, -180, 180],filekey='Global')
all_regions['Tropics'] = rectregion('Tropics',  [-20,20, -180, 180],filekey='Tropics')
all_regions['Southern_Extratropics'] = rectregion('southern_extratropics',  [-90,-20, -180, 180],filekey='S_Extratropics')
all_regions['Northern_Extratropics'] = rectregion('northern_extratropics',  [20,90, -180, 180], filekey='N_Extratropics')
all_regions['Southern_Ocean'] = rectregion('Southern_Ocean', [-90, -40, -180, 180], filekey='S_Ocean')

#"User defined'] = {'coords': [0, 0, 0, 0],

# Right now, this is just used for web page generation. 
#I don't know if it has utility in the currenty diags
region_categories = {
'Polar': ['Alaskan Arctic', 'Antarctica', 'Canadian Arctic', 'Greenland', 'Polar', 'Russian Arctic'],
'Boreal': ['Alaska', 'Central Canada', 'Eastern Canada', 'Eastern Siberian', 'Northern Europe', 'Northwest Canada', 'Western Siberia'],
'Middle Latitudes': ['Central U.S.', 'Eastern U.S.', 'Europe', 'Mediterranean', 'Western U.S.'],
'Tropical Rainforest': ['Amazonia', 'Central Africa', 'Central America', 'Indonesia'],
'Tropical Savanna': ['Brazil', 'India', 'Indochina', 'Sahel', 'Southern Africa'],
'Arid': ['Arabian Peninsula', 'Australia', 'Central Asia', 'Mongolia', 'Sahara Desert', 'Tigris Euphrates'],
'Highland': ['Tibetan Plateau'],
'Asia': ['Central Asia', 'Eastern China', 'Mediterranean and Western Asia', 'Central and Eastern Mongolia and NE China', 'Sahara Desert and Arabian Peninsula', 'Southern Asia', 'Tibetan Plateau'],
'Hemispheric and Global': ['Global Land', 'Northern Hemisphere Land', 'Southern Hemisphere Land']
}

#station ids used in plot set 12
station_names = ["Ascension_Island","Diego_Garcia","Truk_Island", 
                "Western_Europe","Ethiopia","Resolute_Canada","Western_Desert_Australia", 
                "Great_Plains_USA","Central_India","Marshall_Islands","Easter_Island", 
                "McMurdo_Antarctica","SouthPole_Antarctica","Panama","Western_North_Atlantic",
                "Singapore","Manila","Gilbert_Islands","Hawaii","San_Paulo","Heard_Island", 
                "Kagoshima_Japan","Port_Moresby","San_Juan_PR","Western_Alaska", 
                "Thule_Greenland","SanFrancisco_CA","Denver_CO","London_UK","Crete", 
                "Tokyo","Sydney_Australia","Christchurch_NZ","Lima_Peru","Miami_FL","Samoa", 
                "ShipP_GulfofAlaska","ShipC_North_Atlantic","Azores","NewYork_USA",
                "Darwin_Australia","Christmas_Island","Cocos_Islands","Midway_Island", 
                "Raoui_Island","Whitehorse_Canada","OklahomaCity_OK","Gibraltor", 
                "Mexico_City","Recife_Brazil","Nairobi_Kenya","New_Delhi_India", 
                "Madras_India","DaNang_Vietnam","Yap_Island","Falkland_Islands" ]

all_months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
all_seasons = all_months+['ANN', 'DJF', 'MAM', 'JJA', 'SON', 'ASO', 'FMA'] # The last 2 were in some obs sets
all_packages = ['lmwg', 'amwg']


