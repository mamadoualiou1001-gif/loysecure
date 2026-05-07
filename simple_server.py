import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loysecure.settings')

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    
    from wsgiref.simple_server import make_server
    
    print('Démarrage du serveur sur http://127.0.0.1:8001')
    print('Appuyez sur Ctrl+C pour arrêter')
    
    httpd = make_server('127.0.0.1', 8001, application)
    
    # Gestionnaire d'erreurs personnalisé
    def handle_request():
        try:
            httpd.handle_request()
        except Exception as e:
            print(f'\n=== ERREUR LORS DE LA REQUÊTE ===')
            print(f'Type: {type(e).__name__}')
            print(f'Message: {e}')
            traceback.print_exc()
            return False
        return True
    
    # Boucle manuelle
    try:
        while True:
            handle_request()
    except KeyboardInterrupt:
        print('\nServeur arrêté')
        
except Exception as e:
    print(f'Erreur de démarrage: {e}')
    traceback.print_exc()
    input('Appuyez sur Entrée...')
