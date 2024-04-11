import re


def url_builder(url, domain):
    if url.startswith('://'):
        url = 'https' + url
    if not url.startswith('http') and not url.startswith('/'):
        url = '/' + url
    if url.startswith('/'):
        url = f'https://{domain}' + url

    return url


def is_valid_domain(domain):
    pattern = r"^(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,6}$"
    return re.match(pattern, domain) is not None
