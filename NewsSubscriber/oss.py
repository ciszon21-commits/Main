import requests
from django.conf import settings
from datetime import datetime
from django.utils.timezone import make_aware
from .models import OpenAIResponse



def ask_oss(prompt,tag='新聞摘要'):
    url = "https://50-129.sinotech.com.tw:777/api/v1/workspace/openai/chat"

    headers = {
        "Authorization": "Bearer "+settings.ANYTHINGLLM_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "mode": "chat",
        "message":  prompt,
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    ai_response = OpenAIResponse.objects.create(
        request_id=result['id'],
        model='openai-oss-20b',
        content=result['textResponse'],
        created=make_aware(datetime.now()),
        prompt_tokens=result['metrics']['prompt_tokens'],
        completion_tokens=result['metrics']['completion_tokens'],
        total_tokens=result['metrics']['total_tokens'],
        tag=tag,
    )

    return ai_response


