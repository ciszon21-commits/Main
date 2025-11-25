from typing import (
    TypedDict,
    Literal,
)
from django.contrib.auth.models import User

from StudioBase.constants import (
    SINGLE_DOMAIN,
    SINGLE_TOKEN,
)


# TODO 參考用，之後刪除


class UserJson(TypedDict):
    emp_no: 'str'
    emp_no_4: 'str'
    emp_no_5: 'str'
    emp_name: 'str'
    emp_email: 'str'
    emp_dept: 'str'
    emp_dept_name: 'str'
    emp_dept_short_name: 'str'
    emp_company: Literal['A', 'B', 'H',]

def get_user_json(username:'str') -> 'UserJson|None':
    import requests
    url='https://single.sinotech.com.tw/ai/get_info/'

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",  # 或者 "Token" 或者其他根據你的 API 文檔
        "Content-Type": "application/x-www-form-urlencoded"  # 根據需要設置 Content-Type
    }

    data = {
        'emp_no': username.replace('SINOLTD_0','').replace('SINOLTD_','').replace('SINO-TOKEN_','')
    }
    response = requests.post(url, headers=headers, data = data)
    if response.status_code != 200:
        return None
    return response.json()

def get_user_projects(username:'str') -> 'UserJson|None':
    import requests
    url='https://single.sinotech.com.tw/ai/get_user_projects/'

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",  # 或者 "Token" 或者其他根據你的 API 文檔
        "Content-Type": "application/x-www-form-urlencoded"  # 根據需要設置 Content-Type
    }

    data = {
        'emp_no': username.replace('SINOLTD_0','').replace('SINOLTD_','').replace('SINO-TOKEN_','')
    }
    response = requests.post(url, headers=headers, data = data)
    if response.status_code != 200:
        return None
    return response.json()

def get_proj_info(proj_no:'str') -> 'UserJson|None':
    import requests
    url='https://single.sinotech.com.tw/ai/get_project_name/'

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",  # 或者 "Token" 或者其他根據你的 API 文檔
        "Content-Type": "application/x-www-form-urlencoded"  # 根據需要設置 Content-Type
    }

    data = {
        'proj_no': proj_no.upper(),
    }
    response = requests.post(url, headers=headers, data = data)
    if response.status_code != 200:
        return None
    return response.json()


def get_proj_members(proj_no:'str'):
    import requests
    url='https://single.sinotech.com.tw/ai/get_project_members/'

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        'entry_name': proj_no.upper(),
    }
    response = requests.post(url, headers=headers, data = data)
    if response.status_code != 200:
        return None
    return response.json()

def get_empno(email:'str'):
    import requests
    url='https://single.sinotech.com.tw/ai/get_empno/'

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",  # 或者 "Token" 或者其他根據你的 API 文檔
        "Content-Type": "application/x-www-form-urlencoded"  # 根據需要設置 Content-Type
    }

    data = {
        'email': email,
    }
    response = requests.post(url, headers=headers, data = data)
    if response.status_code != 200:
        return None
    return response.json()

def create_user_by_email(email:'str'):
    emp_json = get_empno(email)
    if emp_json['status']=='Error':
        return None
    emp_no = emp_json['emp_no'] if len(emp_json['emp_no'])==5 else "0"+emp_json['emp_no']
    user = User()
    user.username = 'SINO-TOKEN_'+emp_no
    user.email = email
    user.last_name = emp_json['emp_name'][:1]
    user.first_name = emp_json['emp_name'][1:]
    user.set_unusable_password()
    user.save()
    user.refresh_from_db()
    the_user = User.objects.get(email=email)
    the_user.profile
    return the_user

def get_rd():
    import requests
    url='https://single.sinotech.com.tw/ai/get_rd/'

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",  # 或者 "Token" 或者其他根據你的 API 文檔
        "Content-Type": "application/x-www-form-urlencoded"  # 根據需要設置 Content-Type
    }

    response = requests.post(url, headers=headers)
    if response.status_code != 200:
        return None
    return response.json()