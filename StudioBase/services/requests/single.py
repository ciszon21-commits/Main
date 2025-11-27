import re
import requests
from urllib.parse import urljoin

from django.contrib.auth.models import User

from StudioBase.constants import (
    SINGLE_DOMAIN,
    SINGLE_TOKEN,
)
from .types import (
    SingleUser,
    SingleEmpDetail,
    SingleProjectInfo,
    SingleProjectMember,
    SingleEmpNo,
    SingleRD,
)



UN_REPLACE_PATTERN = r'(SINOLTD_|SINO-TOKEN_)'



def get_user_json(username:'str') -> 'SingleUser|None':
    url = urljoin(SINGLE_DOMAIN, '/ai/get_info/')

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",  # 或者 "Token" 或者其他根據你的 API 文檔
        "Content-Type": "application/x-www-form-urlencoded"  # 根據需要設置 Content-Type
    }

    data = {
        'emp_no': re.sub(UN_REPLACE_PATTERN, '', username)
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        return None
    return response.json()

def get_user_emp_detail(username:'str') -> 'SingleEmpDetail|None':
    url = urljoin(SINGLE_DOMAIN, '/ai/get_user_projects/')

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",  # 或者 "Token" 或者其他根據你的 API 文檔
        "Content-Type": "application/x-www-form-urlencoded"  # 根據需要設置 Content-Type
    }

    data = {
        'emp_no': re.sub(UN_REPLACE_PATTERN, '', username)
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        return None
    return response.json()

def get_proj_info(proj_no:'str') -> 'SingleProjectInfo|None':
    url = urljoin(SINGLE_DOMAIN, '/ai/get_project_name/')

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",  # 或者 "Token" 或者其他根據你的 API 文檔
        "Content-Type": "application/x-www-form-urlencoded"  # 根據需要設置 Content-Type
    }

    data = {
        'proj_no': proj_no.upper(),
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        return None
    return response.json()


def get_proj_members(proj_no:'str') -> 'SingleProjectMember|None':
    url = urljoin(SINGLE_DOMAIN, '/ai/get_project_members/')

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        'entry_name': proj_no.upper(),
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        return None
    return response.json()

def get_empno(email:'str') -> 'SingleEmpNo|None':
    url = urljoin(SINGLE_DOMAIN, '/ai/get_empno/')

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",  # 或者 "Token" 或者其他根據你的 API 文檔
        "Content-Type": "application/x-www-form-urlencoded"  # 根據需要設置 Content-Type
    }

    data = {
        'email': email,
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        return None
    return response.json()

# TODO 改去另一個地方
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

def get_rd() -> 'SingleRD|None':
    url = urljoin(SINGLE_DOMAIN, '/ai/get_rd/')

    headers = {
        "Authorization": f"Token {SINGLE_TOKEN}",  # 或者 "Token" 或者其他根據你的 API 文檔
        "Content-Type": "application/x-www-form-urlencoded"  # 根據需要設置 Content-Type
    }

    response = requests.post(url, headers=headers)
    if response.status_code != 200:
        return None
    return response.json()


