import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loysecure.settings')

try:
    from django.core.management import execute_from_command_line
    sys.argv = ['manage.py', 'runserver']
    execute_from_command_line(sys.argv)
except Exception as e:
    print(f'\n=== ERREUR CAPTURÉE ===')
    print(f'Type: {type(e).__name__}')
    print(f'Message: {e}')
    print(f'\nTraceback complet:')
    traceback.print_exc()
    input('\nAppuyez sur Entrée pour continuer...')
