import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix lines 6820-6829 - remove duplicate return JsonResponse
# Line 6820: return JsonResponse({
# Line 6824: return JsonResponse({'error': 'An error occurred'}, status=400)
# Line 6829: }, status=400)

# Replace lines 6820-6829 with a single proper return statement
if 6820 <= len(lines) and 'return JsonResponse({' in lines[6819]:
    # Delete lines 6820-6829 (indices 6819-6828)
    del lines[6819:6829]
    # Insert the corrected line
    lines.insert(6819, "                            return JsonResponse({'error': 'An error occurred'}, status=400)\r\n")
    print("Fixed lines 6820-6829")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
