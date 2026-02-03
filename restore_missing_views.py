import re

# Read urls.py
try:
    with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\urls.py', 'r', encoding='utf-8') as f:
        urls_content = f.read()
except FileNotFoundError:
    print("urls.py not found")
    exit()

# Extract views.func_name
view_names = set(re.findall(r'views\.(\w+)', urls_content))
print(f"Found {len(view_names)} views in urls.py: {view_names}")

# Read views.py
try:
    with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
        views_content = f.read()
except FileNotFoundError:
    print("views.py not found")
    exit()

# Extract existing functions
existing_views = set(re.findall(r'def (\w+)\(', views_content))
print(f"Found {len(existing_views)} views in views.py")

# Find missing
missing = view_names - existing_views
print(f"Missing views: {missing}")

# Generate stubs
stubs = []
for view in missing:
    stubs.append(f"\n@login_required\ndef {view}(request, *args, **kwargs):\n    # Placeholder restored automatically\n    return JsonResponse({{'status': 'success', 'message': 'Function restored as placeholder'}}, status=200)\n")

if stubs:
    with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'a', encoding='utf-8') as f:
        f.writelines(stubs)
    print(f"Appended {len(stubs)} missing views.")

