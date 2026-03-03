import re

path = 'main.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update centerHandle logic (P1/P2 circle, P3 square)
center_pat = re.compile(r"const centerHandle = document\.createElementNS\('http://www\.w3\.org/2000/svg', 'rect'\);.*?centerHandle\.setAttribute\('height', cSize\);", re.DOTALL)
center_repl = """let centerHandle;
        if (index === 0 || index === 1) { // P1 and P2: Solid Circle
            centerHandle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            centerHandle.setAttribute('cx', arc.cx);
            centerHandle.setAttribute('cy', -arc.cy);
            centerHandle.setAttribute('r', handleRadius.toFixed(3));
        } else { // P3: Square
            centerHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            const cSize = handleSize;
            centerHandle.setAttribute('x', arc.cx - cSize/2);
            centerHandle.setAttribute('y', -arc.cy - cSize/2);
            centerHandle.setAttribute('width', cSize);
            centerHandle.setAttribute('height', cSize);
        }"""
content = center_pat.sub(center_repl, content)

# 2. Update sHandle color for P1S (index 0)
s_handle_pat = re.compile(r"if \(index === 0\) \{.*?sHandle\.setAttribute\('fill', 'blue'\);", re.DOTALL)
s_handle_repl = """if (index === 0) { // P1S: Match Arc Color
                sHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                const size = handleSize;
                sHandle.setAttribute('x', pStart.x - size/2);
                sHandle.setAttribute('y', -pStart.y - size/2);
                sHandle.setAttribute('width', size);
                sHandle.setAttribute('height', size);
                sHandle.setAttribute('fill', arc.color); """
content = s_handle_pat.sub(s_handle_repl, content)

# 3. Update eHandle color for P3E (index 2)
e_handle_pat = re.compile(r"if \(index === 2\) \{.*?eHandle\.setAttribute\('fill', 'red'\);", re.DOTALL)
e_handle_repl = """if (index === 2) { // P3E: Match Arc Color
                eHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                const size = handleSize;
                eHandle.setAttribute('x', pEnd.x - size/2);
                eHandle.setAttribute('y', -pEnd.y - size/2);
                eHandle.setAttribute('width', size);
                eHandle.setAttribute('height', size);
                eHandle.setAttribute('fill', arc.color); """
content = e_handle_pat.sub(e_handle_repl, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated main.js markers and colors.")
