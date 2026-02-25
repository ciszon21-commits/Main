---
name: tika
description: Use the internal Tika server to parse files and extract text/metadata.
---

# Tika Skill

This skill allows you to use the internal Apache Tika server to parse various file formats (PDF, DOCX, images, etc.) and extract text and metadata.

## Service Details
- **Base URL**: `http://50-129.sinotech.com.tw:9998/tika`
- **Text Extraction Endpoint**: `/tika` (PUT with file content, returns text)
- **Metadata Endpoint**: `/meta` (PUT with file content, returns JSON metadata)
- **Recursive Metadata/Text**: `/rmeta/text` (PUT with file content, returns detailed JSON with text)

## Usage

To use this skill, you should write a Python script using the `requests` library to interact with the Tika server.

### Example: Extracting Text from a File

```python
import requests

def parse_with_tika(file_path):
    tika_url = 'http://50-129.sinotech.com.tw:9998/tika'
    headers = {'Accept': 'text/plain'}
    
    try:
        with open(file_path, 'rb') as f:
            response = requests.put(tika_url, headers=headers, data=f)
            response.raise_for_status()
            return response.text
    except Exception as e:
        return f"Error parsing file: {e}"

# Example usage
# print(parse_with_tika('path/to/your/document.pdf'))
```

### Example: Extracting Metadata and Text (JSON)

```python
import requests
import json

def parse_rmeta(file_path):
    tika_url = 'http://50-129.sinotech.com.tw:9998/rmeta/text'
    headers = {'Accept': 'application/json'}
    
    try:
        with open(file_path, 'rb') as f:
            response = requests.put(tika_url, headers=headers, data=f)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

# The output is a list of dictionaries (one for the main document, others for embedded objects if any)
# result = parse_rmeta('path/to/file.docx')
# if result and isinstance(result, list):
#     print(result[0].get('X-TIKA:content', 'No content'))
```

## Best Practices
- Always check the response status code.
- Handle large files carefully; the server limits might apply.
- The server is only accessible within the internal network.
