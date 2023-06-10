import urllib.request


def is_valid(url):
    try:
        urllib.request.urlopen(url)
        return True
    except Exception:
        return False
