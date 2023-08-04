import requests
from bs4 import BeautifulSoup


url = 'https://stackoverflow.com/questions/11754478/sending-a-http-request-that-tells-server-to-return-only-headers-and-no-body'
res = requests.get(url)

assert res.status_code == 200, 'Error request'


soup = BeautifulSoup(res.text, 'lxml')

print(f'{soup.head.title.text=}\n\n')
for index, meta in enumerate(soup.select('head meta')):
    print(f'{index=} ---- {meta}\n\n')

with open('index.html', 'w') as f:
    f.write(res.text)