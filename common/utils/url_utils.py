def url_builder(url, domain):
    if url.startswith('://'):
        url = 'https' + url
    if not url.startswith('http') and not url.startswith('/'):
        url = '/' + url
    if url.startswith('/'):
        url = f'https://{domain}' + url

    return url

