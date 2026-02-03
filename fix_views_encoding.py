import sys

# Read the file
input_file = 'd:/10.vibecoding/CoDevStudio-07729/EngineerRPG/views.py'
output_file = 'd:/10.vibecoding/CoDevStudio-07729/EngineerRPG/views_fixed.py'

try:
    # Read as binary
    with open(input_file, 'rb') as f:
        raw_content = f.read()
    
    # Decode with replacement
    content = raw_content.decode('utf-8', errors='replace')
    
    # Process line by line
    lines = content.split('\n')
    fixed_lines = []
    fixed_count = 0
    
    for i, line in enumerate(lines):
        # Check if line contains any problematic characters
        if '\ufffd' in line or any(ord(c) > 127 and ord(c) < 256 for c in line):
            # Check if it's a docstring or comment
            stripped = line.lstrip()
            if stripped.startswith('"""') or stripped.startswith("'''") or stripped.startswith('#'):
                # Replace with generic comment
                indent = len(line) - len(stripped)
                if stripped.startswith('"""'):
                    fixed_lines.append(' ' * indent + '"""Function docstring"""')
                elif stripped.startswith("'''"):
                    fixed_lines.append(' ' * indent + "'''Function docstring'''")
                else:
                    fixed_lines.append(' ' * indent + '# Comment')
                fixed_count += 1
                print(f"Fixed line {i+1}: {repr(line[:50])}")
            else:
                # Not a comment, keep it but remove bad chars
                fixed_line = line.replace('\ufffd', '')
                fixed_lines.append(fixed_line)
        else:
            # Line is fine
            fixed_lines.append(line)
    
    # Write fixed content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"\nFixed {fixed_count} lines")
    print(f"Output: {output_file}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
