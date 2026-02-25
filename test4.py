import os
import django
import inspect

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoDevStudio.settings")
django.setup()

from EngineerRPG.views import api_auto_layout_skill_tree

def run_test():
    unwrapped = api_auto_layout_skill_tree
    while hasattr(unwrapped, '__wrapped__'):
        unwrapped = unwrapped.__wrapped__
        
    print(inspect.getsource(unwrapped))

if __name__ == '__main__':
    run_test()
