import string

possible_keys = list(string.ascii_lowercase)
size = 1
def splitList(keys, size):
    subLists = []
    for i in xrange(0, len(keys), size):
        subLists += [keys[i:i+size]]
    return subLists
sublistSize = len(possible_keys)/size
x = splitList(possible_keys, sublistSize)