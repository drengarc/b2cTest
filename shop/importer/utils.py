import urllib

has_variable_name = lambda x: x.find("[") > 0


def more_than_one_index(s, brackets=2):
    '''
    Search for two sets of [] []
    @param s: string to search
    '''
    start = 0
    brackets_num = 0
    while start != -1 and brackets_num < brackets:
        start = s.find("[", start)
        if start == -1:
            break
        start = s.find("]", start)
        brackets_num += 1
    if start != -1:
        return True
    return False


def get_key(s):
    '''
    Get data between [ and ] remove ' if exist
    @param s: string to process
    '''
    start = s.find("[")
    end = s.find("]")
    if start == -1 or end == -1:
        return None
    if s[start + 1] == "'":
        start += 1
    if s[end - 1] == "'":
        end -= 1
    return s[start + 1:end]  # without brackets


is_number = lambda s: s[1:].isdigit() if len(s) > 0 and s[0] in ('-', '+') else s.isdigit()


def parser_helper(key, val):
    '''
    Helper for parser function
    @param key:
    @param val:
    '''
    start_bracket = key.find("[")
    end_bracket = key.find("]")
    pdict = {}
    if has_variable_name(key):  # var['key'][3]
        pdict[key[:key.find("[")]] = parser_helper(key[start_bracket:], val)
    elif more_than_one_index(key):  # ['key'][3]
        newkey = get_key(key)
        newkey = int(newkey) if is_number(newkey) else newkey
        pdict[newkey] = parser_helper(key[end_bracket + 1:], val)
    else:  # key = val or ['key']
        newkey = key
        if start_bracket != -1:  # ['key']
            newkey = get_key(key)
            if newkey is None:
                raise Exception("malformed urlencode")
        newkey = int(newkey) if is_number(newkey) else newkey
        val = int(val) if is_number(val) else val
        pdict[newkey] = val
    return pdict


def parse(query_string, unquote=True):
    '''
    Main parse function
    @param query_string:
    @param unquote: unquote html query string ?
    '''
    mydict = {}
    plist = []
    if query_string == "":
        return mydict
    for element in query_string.split("&"):
        try:
            if unquote:
                (var, val) = element.split("=")
                var = urllib.unquote_plus(var)
                val = urllib.unquote_plus(val)
            else:
                (var, val) = element.split("=")
        except ValueError:
            raise Exception("malformed urlencode")
        plist.append(parser_helper(var, val))
    for di in plist:
        (k, v) = di.popitem()
        tempdict = mydict
        while k in tempdict and type(v) is dict:
            tempdict = tempdict[k]
            (k, v) = v.popitem()
        if k in tempdict and type(tempdict[k]).__name__ == 'list':
            tempdict[k].append(v)
        elif k in tempdict:
            tempdict[k] = [tempdict[k], v]
        else:
            tempdict[k] = v
    return mydict