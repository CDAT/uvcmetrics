def findfile(directory, prefix, season):
    import os
    DIRECTORY = os.listdir(directory)
    for file in DIRECTORY:
        if file.startswith(prefix) and season in file:
            return file
    return None
