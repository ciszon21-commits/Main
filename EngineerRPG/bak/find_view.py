
import os

try:
    with open(r'e:\rexProgram\train-vibe\CoDevStudio\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if 'def manage_skill_tree' in line:
                print(f'Found at line {i+1}: {line.strip()}')
except Exception as e:
    print(e)
