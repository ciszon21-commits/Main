import os

from UserProfile import models as UserModels
from . import models
from . import model_method_implements as implements
from . import pmis_function as PmisFunc



class SSO_Token:
    def user(self):
        empMail = models.EmpidEmail.objects.filter(email=self.LoginUser)
        return empMail.first() if empMail else None
    def format(self:'models.SSO_Token') -> 'dict':
        tenders = self.get_tenders()
        result = self.get_tender_detail(tenders)
        return result
    def get_tenders(self:'models.SSO_Token') -> 'list[str]':
        if not self.Roles: return []
        roles = self.Roles.split(',')
        tenderNos = [r for r in roles if r.lower().startswith('tender')]
        return tenderNos
    def get_proj_tender_no(self:'models.SSO_Token', tender:'str') -> 'list[str]':
        projNo = '%s-%s' %(self.Project, tender)
        fptNo = PmisFunc.formatProjNo(projNo)
        return fptNo.get('fullNo')
    def get_proj_tender_nos(self:'models.SSO_Token', tenders:'list[str]'=None) -> 'list[str]':
        tenders = self.get_tenders() if tenders is None else tenders
        return [self.get_proj_tender_no(t) for t in tenders]
    def get_tender_detail(self:'models.SSO_Token', tenders:'list[str]'=None) -> 'dict':
        tenders = self.get_tenders() if tenders is None else tenders
        result = {}
        result['no_tender'] = len(tenders) == 0
        result['only_one'] = len(tenders) == 1
        if result['only_one']:
            result.update(self.get_one_tender_detail(tenders[0]))
        else:
            result.update(self.get_multiple_tender_detail(tenders))
        return result
    def get_one_tender_detail(self:'models.SSO_Token', tender:'str'=None) -> 'dict':
        ptNo = self.get_proj_tender_no(tender)
        return {
            'tender_no': tender,
            'proj_tender_no': ptNo,
        }
    def get_multiple_tender_detail(self:'models.SSO_Token', tenders:'list[str]'=None) -> 'dict':
        ptNos = self.get_proj_tender_nos(tenders)
        return {
            'tender_nos': tenders,
            'proj_tender_nos': ptNos,
        }







class DocCollab_DBStorePath:
    def db_data(self:'models.DocCollab_DBStorePath') -> dict:
        return implements.formatConnectionString(self)
    def get_home_page(self:'models.DocCollab_DBStorePath'):
        if not self.HomePage: return ''
        return self.HomePage.replace(' ', '')
    def get_home_page_redirect(self:'models.DocCollab_DBStorePath'):
        homePage = self.get_home_page()
        return '%s/BaseApp/Redirect.aspx?redirect=' %(homePage)



class LineGroupMapping:
    def get_first_message(self:'models.LineGroupMapping') -> 'models.LineGroupMapping':
        messages = models.LineMessage.objects.filter(GroupId=self.Id)
        messages = messages.order_by('CreateDate')
        return messages.first()
    def get_last_message(self:'models.LineGroupMapping') -> 'models.LineMessage':
        messages = models.LineMessage.objects.filter(GroupId=self.Id)
        messages = messages.order_by('CreateDate')
        return messages.last()

class LineMessage:
    def user(self):
        return models.LineUser.objects.filter(UserId=self.UserId).first()
    def time(self):
        return self.CreateDate
    def group_mapping(self:'models.LineMessage') -> 'models.LineGroupMapping':
        return models.LineGroupMapping.objects.filter(Id=self.GroupId).first()
    def doc_dbsp(self:'models.LineMessage') -> 'models.DocCollab_DBStorePath':
        gm = self.group_mapping()
        return models.DocCollab_DBStorePath.objects.filter(EntryName=gm.Project).first()
    def get_file_uid(self:'models.LineMessage'):
        if self.ImageUID: return self.ImageUID
        if self.FileUID: return self.FileUID
        return None
    def get_image_path(self:'models.LineMessage'):
        if not self.ImageUID: return None
        filename = '%s.png' %(self.ImageUID)
        path = implements.formatLineMessageFilePath(self, filename)
        if path: return path
        path = implements.getArchiveLineMessageFilePath(self, filename)
        if path: return path
        return ''
    def get_file_path(self:'models.LineMessage'):
        if not self.FileUID: return None
        filename = '%s%s' %(self.FileUID, self.ExtName)
        path = implements.formatLineMessageFilePath(self, filename)
        if path: return path
        path = implements.getArchiveLineMessageFilePath(self, filename)
        if path: return path
        return ''
    def get_db_datas(self:'models.LineMessage') -> dict:
        dbsp = self.doc_dbsp()
        if not dbsp: return {}
        return dbsp.db_data()
    def get_base_file(
            self: 'models.LineMessage',
            uid: 'str' = None,
        ) -> 'models.BaseFile':
        datas = self.get_db_datas()
        uid = uid if uid else self.get_file_uid()
        if not datas: return None
        if not uid: return None
        host = datas.get('Data Source', '')
        dbname = datas.get('Initial Catalog', '')
        username = datas.get('User ID', '')
        password = datas.get('Password', '')
        return models.BaseFile.objects(host=host, name=dbname, username=username, password=password).get(UID=uid)