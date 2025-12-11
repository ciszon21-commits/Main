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

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text[:200]}")
            # Return a dummy object or raise specific error depending on needs
            # For now, return a dummy object to prevent attribute errors downstream
            return _create_dummy_response(prompt, tag, f"Error: API status {response.status_code}")

        try:
            result = response.json()
        except ValueError as e:
            print(f"Error: Failed to parse JSON response. {e}")
            print(f"Response content: {response.text[:200]}")
            return _create_dummy_response(prompt, tag, "Error: Invalid JSON response")

        ai_response = OpenAIResponse.objects.create(
            request_id=result.get('id', 'unknown'),
            model='openai-oss-20b',
            content=result.get('textResponse', ''),
            created=make_aware(datetime.now()),
            prompt_tokens=result.get('metrics', {}).get('prompt_tokens', 0),
            completion_tokens=result.get('metrics', {}).get('completion_tokens', 0),
            total_tokens=result.get('metrics', {}).get('total_tokens', 0),
            tag=tag,
        )

        return ai_response

    except requests.exceptions.RequestException as e:
        print(f"Error: API request failed. {e}")
        return _create_dummy_response(prompt, tag, f"Error: Request failed - {str(e)}")
    except Exception as e:
        print(f"Error: Unexpected error in ask_oss. {e}")
        return _create_dummy_response(prompt, tag, f"Error: Unexpected error - {str(e)}")

def _create_dummy_response(prompt, tag, error_message):
    """Create a dummy OpenAIResponse object for error cases"""
    return OpenAIResponse.objects.create(
        request_id='error',
        model='error',
        content=error_message,
        created=make_aware(datetime.now()),
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        tag=tag,
    )


