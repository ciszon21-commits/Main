from django.contrib.auth import login
from django.contrib.auth.models import User
from Extension.SinoUser import create_user_by_email

def check_pmis_token(request, token:'str'):
    import requests
    url='https://engex1.sinotech.com.tw/Survey/CheckToken.ashx?uid='
    
    response = requests.post(url+token, verify=False)
    if response.status_code != 200:
        return None
    
    result=response.json()
    user = User.objects.filter(email=result['LoginUser']).first()
    if user:        
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    else:
        user = create_user_by_email(result['LoginUser'])
        if user:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return result['Project']