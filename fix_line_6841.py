import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix lines 6837-6847 - nested return JsonResponse
# Line 6837: return JsonResponse({
# Line 6841: return JsonResponse({'error': 'An error occurred'}, status=400)
# Line 6847: }, status=400)

start_index = 6836 # 0-indexed (line 6837)
end_index = 6847   # 0-indexed (line 6848)

# Check if the pattern matches what we expect
if start_index < len(lines) and 'return JsonResponse({' in lines[start_index]:
    # Delete the block
    del lines[start_index:end_index]
    # Insert the corrected line
    lines.insert(start_index, "                            return JsonResponse({'error': 'An error occurred'}, status=400)\r\n")
    print("Fixed lines 6837-6847")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
