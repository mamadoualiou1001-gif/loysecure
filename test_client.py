import http.client

try:
    conn = http.client.HTTPConnection('127.0.0.1', 8001)
    conn.request('GET', '/')
    response = conn.getresponse()
    print(f'Status: {response.status}')
    print(f'Response: {response.read().decode()[:500]}')
except Exception as e:
    print(f'Erreur connexion: {e}')
    import traceback
    traceback.print_exc()
