import requests
from urllib.parse import urljoin

from StudioBase.constants import (
    PMIS_DOMAIN,
)

from .types import PMISUser



def pmis_token_user(token:'str') -> 'PMISUser|None':
    if not token:
        return None
    url = urljoin(PMIS_DOMAIN, '/Survey/CheckToken.ashx')
    params = {
        'uid': token,
    }
    response = requests.post(url, params=params, verify=False)
    if response.status_code != 200:
        return None
    return response.json()



