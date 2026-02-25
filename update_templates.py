import os
import glob

template_dir = 'EngineerRPG/templates/EngineerRPG/**/*.html'
files = glob.glob(template_dir, recursive=True)

# Replacements Dictionary
replacements = {
    "公會": "公司",
    "隊伍": "部門",
    "隊長": "部門主管",
    "副隊長": "部門副主管",
    "創世神": "幹部",       # Just in case there are static mentions
    "公會會長": "董事長",
    "公會幹部": "幹部",
}

for filepath in files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = content
        for old, new in replacements.items():
            new_content = new_content.replace(old, new)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
    except Exception as e:
        print(f"Failed {filepath}: {e}")

print("Template strings replaced successfully.")
