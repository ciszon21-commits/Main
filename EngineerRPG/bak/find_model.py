
try:
    with open(r'e:\rexProgram\train-vibe\CoDevStudio\EngineerRPG\models.py', 'r', encoding='utf-8') as f:
        iterator = enumerate(f)
        for i, line in iterator:
            if 'class PromotionRequest' in line:
                print(f'Found at line {i+1}: {line.strip()}')
                for j in range(20):
                    try:
                        print(next(iterator)[1].strip())
                    except StopIteration:
                        break
                break
except Exception as e:
    print(e)
