def _makeHexStr(a):
    return format(a, '#04x')
def _generateTenAccounts():
    prefixes = [_makeHexStr(i) for i in range(10)]
    postfix = "195c933ff445314e667112ab22f4a7404bad7f9746564eb409b9bb8c6aed32"
    return [prefix + postfix for prefix in prefixes]
tenAccounts = _generateTenAccounts()
