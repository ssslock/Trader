import ccxt

apis = {}

def get_api(name):
    api = apis.get(name)
    if api == None:
        api = getattr(ccxt, name)()
        api.load_markets()
        apis[name] = api
    return api
