import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get('https://guiamedico.cremesp.org.br/main-es2015.a7bd9d7cdd0f2c211841.js', headers=headers, timeout=10)
idx = r.text.find('api.cremesp.org.br/guia-medico')
while idx != -1:
    print(r.text[max(0, idx-100):idx+250])
    print("="*40)
    idx = r.text.find('api.cremesp.org.br/guia-medico', idx+1)
