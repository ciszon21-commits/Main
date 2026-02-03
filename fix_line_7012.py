import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix lines 7007-7017 - nested return JsonResponse
# Line 7007: return JsonResponse({
# Line 7011: str return JsonResponse({'error': 'An error occurred'}, status=400)
# Line 7017: }, status=400)

start_index = 7006 # 0-indexed (line 7007)
end_index = 7017   # 0-indexed (line 7018)

# Check if the pattern matches what we expect
if start_index < len(lines) and 'return JsonResponse({' in lines[start_index]:
    # Delete the block
    del lines[start_index:end_index]
    # Insert the corrected line
    lines.insert(start_index, "                        return JsonResponse({'error': 'An error occurred'}, status=400)\r\n")
    print("Fixed lines 7007-7017")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
