import requests
from typing import TypedDict

from SinoExtension.tools import (
    is_email,
    url_join,
)

from SinoAuthService.types import UserDetailJson

from StudioBase.constants import (
    SINO_AUTH_SERVICE_TOKEN,
    SINO_AUTH_SERVICE_DOMAIN,
    SINO_AUTH_SERVICE_APP_PATH,
)



class Output(TypedDict):
    status: 'int'
    message: 'str'
    response: 'requests.Response'


BAD_INPUT_MSG = '%s 對於 %s 而言是必須的。'
UNAUTH_MSG = '必須要設置 %s 才可以使用功能 %s。'
SAS_TOKEN_FN = 'settings.SINO_AUTH_SERVICE_TOKEN'


def get_user_json(email:'str'=None, emp_no:'str|int'=None, output:'Output'={}) -> 'UserDetailJson|None':
    if not SINO_AUTH_SERVICE_TOKEN:
        output['status'] = 401
        output['message'] = UNAUTH_MSG %(SAS_TOKEN_FN, get_user_json.__qualname__)
        return None
    if (
        (email and not is_email(email))
        or (emp_no and not str(emp_no).isnumeric())
        or (not email and not emp_no)
    ):
        output['status'] = 400
        output['message'] = BAD_INPUT_MSG %('emp_no or email', get_user_json.__qualname__)
        return None
    url = url_join(SINO_AUTH_SERVICE_DOMAIN, SINO_AUTH_SERVICE_APP_PATH, '/user/detail/')
    headers = {
        'Authorization': f'Token {SINO_AUTH_SERVICE_TOKEN}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'email': email,
        'emp_no': emp_no,
    }
    response = requests.get(url, headers=headers, params=data)
    if response.status_code != 200:
        output['status'] = response.status_code
        output['message'] = response.text
        output['response'] = response
        return None
    return response.json()


