from typing import (
    TypedDict,
    Literal,
)



class PMISUser(TypedDict):
    LoginUser: 'str'
    Project: 'list[str]'




class SingleUser(TypedDict):
    emp_no: 'str'
    emp_no_4: 'str'
    emp_no_5: 'str'
    emp_name: 'str'
    emp_email: 'str'
    emp_dept: 'str'
    emp_dept_name: 'str'
    emp_dept_short_name: 'str'
    emp_company: Literal['A', 'B', 'H',]



class SingleEmpDetail(TypedDict):
    emp_no: 'str'
    emp_no_4: 'str'
    emp_no_5: 'str'
    emp_name: 'str'
    emp_email: 'str'
    emp_dept: 'str'
    emp_dept_name: 'str'
    emp_dept_short_name: 'str'
    emp_company: 'str'
    projects: 'str'
    duty: 'str'


class SingleProjectInfo(TypedDict):
    name: 'str'
    manager: 'str'
    supervise: 'str'
    director: 'str'


class SingleProjectMember(TypedDict):
    Name: 'str'
    Email: 'str'


class SingleEmpNo(TypedDict):
    status: 'str'
    emp_no: 'str'
    emp_name: 'str'


class SingleRD(TypedDict):
    proj_no: 'str'
    proj_name_add: 'str'
    start_date: 'str'
    target_date: 'str'
    buget: 'int'



