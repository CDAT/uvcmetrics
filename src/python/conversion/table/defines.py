# A set of global variables (more or less) defining things that lots of
# pieces of diags use/can use.

# Coordinates from maps generated for lnd diags, obs set 3 from NCAR -
# http://www.cgd.ucar.edu/tss/clm/diagnostics/clm4cn/i1860-2009cnGCPs3-obs/set3/set3.html

all_regions = {}
all_regions['Alaskan_Arctic'] = [66, 72, -170, -140]
all_regions['Antarctica'] = [-90, -65, -180, 180]
all_regions['Canadian_Arctic'] = [66, 90, -120, -60]
all_regions['Greenland'] =  [60, 90, -60, -20]
all_regions['Polar'] = [60, 90, -180, 180]
all_regions['Russian_Arctic'] = [66, 90, 70, 170]
all_regions['Alaska'] = [59, 67, -170, -140]
all_regions['Central_Canada'] = [50, 62, -100, -80]
all_regions['Eastern_Canada'] = [50, 60, -80, -55]
all_regions['Eastern_Siberia'] = [50, 67, 90, 140]
all_regions['Northern_Europe'] = [60, 70, 5, 45]
all_regions['Northwest_Canada'] = [55, 67, -125, -100]
all_regions['Western_Siberia'] = [55, 67, 60, 90]
all_regions['Central_U.S.'] = [30, 50, -105, -90]
all_regions['Eastern_U.S.'] = [30, 50, -90, -70]
all_regions['Europe'] = [45, 60, -10, 30]
all_regions['Mediterranean'] = [34, 45, -10, 30]
all_regions['Western_U.S.'] = [30, 50, -130, -105]
all_regions['Amazonia'] = [-10, 0, -70, -50]
all_regions['Central_Africa'] = [-5, 5, 10, 30]
all_regions['Central_America'] = [5, 16, -95, -75]
all_regions['Indonesia'] =[-10, 10, 90, 150]
all_regions['Brazil'] = [-24, -10, -65, -30]
all_regions['India'] = [10, 24, 70, 90]
all_regions['Indochina'] = [10, 24, 90, 120]
all_regions['Sahel'] = [6,16,-5,15]
all_regions['Southern_Africa'] = [-25, -5, 10, 40]
all_regions['Arabian_Peninsula'] = [16, 30, 35, 60]
all_regions['Australia'] = [-30, -20, 110, 145]
all_regions['Central_Asia'] = [35, 50, 55, 70]
all_regions['Mongolia'] = [40, 50, 85, 120]
all_regions['Sahara_Desert'] = [16, 30, -20, 30]
all_regions['Tigris_Euphrates'] = [30, 40, 37, 50]
all_regions['Tibetan_Plateau'] =  [30, 40, 80, 100]
all_regions['Central_Asia'] =  [40, 50, 40, 100]
all_regions['Eastern_China'] = [30, 40, 100, 120]
all_regions['Mediterranean_and_Western_Asia'] = [30, 45, -10, 60]
all_regions['Central_and_Eastern_Mongolia_and_NE_China'] = [40, 50, 100, 130]
all_regions['Sahara_Desert_and_Arabian_Peninsula'] =  [15, 30, -15, 60]
all_regions['Southern_Asia'] = [20, 30, 60, 120]
all_regions['Tibetan_Plaeau'] = [30, 40, 80, 100]
all_regions['N_Hemisphere_Land'] =  [0, 90, -180, 180]
all_regions['S_Hemisphere_Land'] = [-90, 0, -180, 180]
all_regions['Global'] = [-90, 90, -180, 180]
all_regions['Tropics'] = [-40,40, -180, 180]
all_regions['Southern_Extratropics'] =  [-90,-40, -180, 180]
all_regions['Northern_Extratropics'] =  [40,90, -180, 180]
all_regions['Southern_Ocean'] = [-90, -40, -180, 180]


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
just_seasons = ['DJF', 'MAM', 'JJA', 'SON', 'ASO', 'FMA'] # The last 2 were in some obs sets
all_seasons = all_months+just_seasons+['ANN']
all_packages = ['lmwg', 'amwg']


