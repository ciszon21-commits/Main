import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix lines 7008-7018 - nested return JsonResponse
# Line 7008: return JsonResponse({ (index 7007)
# Line 7012: return JsonResponse({'error': 'An error occurred'}, status=400)
# Line 7018: }, status=400) (index 7017)

# Indices based on recent view_file
start_index = 7007
end_index = 7018 # Slice is exclusive at end, so 7018 means up to index 7017

# Verify content before applying
if start_index < len(lines) and 'return JsonResponse({' in lines[start_index]:
    # Delete the block
    del lines[start_index:end_index]
    # Insert the corrected line
    lines.insert(start_index, "                        return JsonResponse({'error': 'An error occurred'}, status=400)\r\n")
    print("Fixed lines 7008-7018")
else:
    print(f"Target line mismatch. Found: {lines[start_index] if start_index < len(lines) else 'EOF'}")

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done")
