def dict_keys(dict):
    return { k:v.get() for k,v in dict.items() }

def results(results):
    return [ r.get() for r in results ]
