regions = {
    'Global': (-90, 90),
    #            'Tropics (20S-20N)':(-20,20),
    'Tropics': (-20, 20),
    #            'Southern_Extratropics (90S-20S)':(-90,-20),
    'Southern_Extratropics': (-90, -20),
     #            'Northern_Extratropics (20N-90N)':(20,90),
    'Northern_Extratropics': (20, 90)
}
regions_reversed = {
    (-90, 90): 'Global',
    (-20, 20): 'Tropics',
    (-90, -20): 'Southern_Extratropics',
    (20, 90): 'Northern_Extratropics'
}