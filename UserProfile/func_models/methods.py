from SinoExtension.tools import (
    model_update,
)

from django.contrib.auth.models import User

from .. import models





class UserMethod:
    def get_profile(self) -> 'models.UserProfile|None':
        profile = models.UserProfile.objects.filter(user=self).first()
        if profile:
            return profile
        return self.create_user_profile()

    def get_full_name(self:'User', *args, **kwargs):
        profile:'models.UserProfile' = self.profile
        if self.is_superuser and not profile:
            return self.username
        else:
            return profile.get_full_name()

    def create_user_profile(self:'User') -> 'models.UserProfile|None':
        from Extension.SinoUser import get_user_json
        user_json = get_user_json(self.username)
        if not user_json:
            return None
        profile = models.UserProfile()
        return model_update(profile, user=self, **user_json)





class UserProfileMethod:
    def get_emp_company(self:'models.UserProfile') -> 'str':
        db = {
            'A': '中興',
            'B': '環興',
            'H': '華興',
        }
        return db.get(self.emp_company, '公司')
    def get_emp_dept(self:'models.UserProfile') -> 'str':
        db = {
            '01': '監理',
            '02': '業務及契約部',
            '03': '行政部',
            '04': '考核部',
            '06': '研發及資訊部',
            '08': '財會部',
            '11': '水利工程部',
            '12': '電力及能源工程部',
            '14': '軌道工程一部',
            '15': '環境工程部',
            '18': '建築工程部',
            '22': '園區及路航工程部',
            '23': '法務室',
            '24': '軌道工程二部',
            '25': '職業安全衛生管理中心',
            '28': '核能後端專案計畫',
            '31': '結構工程部',
            '32': '大地工程部',
            '33': '機械工程部',
            '34': '系統及電氣工程部',
            '39': '工程管理部',
            '40': '機電監造工程部',
            '41': '機場專案',
            '42': '桃園航空城監造工程處',
            '43': '桃機安置宅工程處',
            '44': '台電大潭梅湖工程處',
            '45': '台電台區工程處',
            '46': '花東鐵路雙軌南段工程處',
            '48': '桃園鐵路地下化工程處',
            '50': '華興',
            '54': '台電興達電廠工程處',
            '55': '新北塭仔圳工程處',
            '56': '花東縱谷工程處',
            '57': '機場捷運延伸線工程處',
            '58': '南港機廠工程處',
            '59': '中部工程中心',
            '60': '高雄地鐵工程處',
            '65': '桃捷綠線專管暨監造專案',
            '66': '桃捷綠線土建監造工程處',
            '67': '桃捷綠線機電監造工程處',
            '68': '豐原潭子段工程處',
            '69': '淡江大橋工程處',
            '70': '三鶯捷運工程處',
            '88': '機場捷運機電工程處',
            '92': '南部工程中心',
            '98': '台電大林工程處',
            'A1': '桃機第三跑道工程處',
            'A2': '國1后里大雅工程處',
        }
        return db.get(self.emp_dept, '部門')
    def get_full_name(self:'models.UserProfile') -> 'str':
        return '%s-%s-%s' %(
            self.get_emp_company(),
            self.get_emp_dept(),
            self.emp_name,
        )
    def get_own_projects(self:'models.UserProfile') -> 'str':
        from Extension.SinoUser import get_user_projects
        projs = get_user_projects(self.username)
        return projs
    def get_user_title(self:'models.UserProfile') -> 'str':
        from Extension.SinoUser import get_user_title
        title = get_user_title(self.username)
        return title




