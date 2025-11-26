from django.db import models


from . import model_managers as managers
from . import model_methods as method

class EmpidEmail(models.Model):
    class Meta:
        app_label= 'PMIS'
        db_table = 'EmpidEmail'
        managed = False
    UID = models.CharField(primary_key=True, max_length=255)
    CreateDate = models.DateTimeField()
    empid = models.ImageField(default=0)
    EmpName = models.CharField(max_length=20, default='')
    email = models.CharField(max_length=225, default='')
    leave = models.BooleanField()
    memo = models.CharField(max_length=225, default='')

class SSO_Token(models.Model, method.SSO_Token):
    class Meta:
        app_label = 'PMIS'
        db_table = 'SSO_Token'
        managed = False
    Token = models.CharField(primary_key=True, max_length=255)
    GotoApp = models.CharField(max_length=100, default='')
    Project = models.CharField(max_length=100, default='')
    LoginUser = models.CharField(max_length=225, default='')
    LoginDate = models.DateTimeField()
    Roles = models.CharField(max_length=225, default='')
    UserName = models.CharField(max_length=225, default='')

class CenterDept(models.Model):
    class Meta:
        app_label = 'PMIS'
        db_table = 'CenterDept'
        managed = False
    CenterNo = models.CharField(max_length=5)
    DeptNo = models.CharField(max_length=5, primary_key=True)
    DeptName = models.CharField(max_length=24)
    DeptShortName = models.CharField(max_length=18)
    Director = models.CharField(max_length=4)
    CompanyNo = models.CharField(max_length=1)

class EmpSubCompany(models.Model):
    class Meta:
        app_label = 'PMIS'
        db_table = 'EmpSubCompany'
        managed = False
    EmpNo = models.CharField(primary_key=True, max_length=100)
    EmpName = models.CharField(max_length=100)
    email = models.CharField(max_length=225)
    DeptName = models.CharField(max_length=100)

class DocCollab_DBStorePath(models.Model, method.DocCollab_DBStorePath):
    class Meta:
        app_label = 'PMIS'
        db_table = 'DocCollab_DBStorePath'
        managed = False
    EntryName = models.CharField(primary_key=True, max_length=100)
    ConnectionString = models.CharField(max_length=500, default='')
    HomePage = models.CharField(max_length=500, default='')
    HttpRequestUrl = models.CharField(max_length=500, default='')
    CreateDate = models.CharField(max_length=500, default='')
    WebsiteName = models.CharField(max_length=500, default='')
    AuthenticationMode = models.CharField(max_length=500, default='')
    EnableFreeSpace = models.BooleanField(default=None, blank=True, null=True)
    EnableArchive = models.BooleanField(default=None, blank=True, null=True)
    EnableArchivePre = models.BooleanField(default=None, blank=True, null=True)
    IsPMIS = models.BooleanField(default=None, blank=True, null=True)
    IsEM = models.BooleanField(default=None, blank=True, null=True)
    TDays = models.IntegerField(default=None, blank=True, null=True)
    TActivity = models.IntegerField(default=None, blank=True, null=True)
    TAccount = models.IntegerField(default=None, blank=True, null=True)
    YearDays = models.IntegerField(default=None, blank=True, null=True)
    YearActivity = models.IntegerField(default=None, blank=True, null=True)
    Ignore = models.BooleanField(default=None, blank=True, null=True)
    Department = models.CharField(max_length=500, null=True, default='')
    Gmail_Adress = models.CharField(max_length=500, null=True, default='')
    HttpRequestUrl_File = models.CharField(max_length=500, default='')
    IsIPLimit = models.BooleanField(default=None, blank=True, null=True)
    Closed = models.BooleanField(default=None, blank=True, null=True)
    BimModel = models.BooleanField(default=None, blank=True, null=True)
    LeafNum = models.IntegerField(default=None, blank=True, null=True)
    FileNum = models.IntegerField(default=None, blank=True, null=True)
    TaskNum = models.IntegerField(default=None, blank=True, null=True)
    MeetingNum = models.IntegerField(default=None, blank=True, null=True)
    MessageNum = models.IntegerField(default=None, blank=True, null=True)
    InBookNum = models.IntegerField(default=None, blank=True, null=True)
    OutBookNum = models.IntegerField(default=None, blank=True, null=True)
    InBookDelayNum = models.IntegerField(default=None, blank=True, null=True)
    ArchiveNG = models.IntegerField(default=None, blank=True, null=True)
    FreeSpaceNG = models.IntegerField(default=None, blank=True, null=True)
    K_DirNum = models.IntegerField(default=None, blank=True, null=True)
    K_FileNum = models.IntegerField(default=None, blank=True, null=True)
    K_ModFileNum = models.IntegerField(default=None, blank=True, null=True)
    MailInNum = models.IntegerField(default=None, blank=True, null=True)
    MailOutNum = models.IntegerField(default=None, blank=True, null=True)
    MailForwardNum = models.IntegerField(default=None, blank=True, null=True)
    ContinueWhenClosed = models.BooleanField(default=None, blank=True, null=True)
    ProjectState = models.CharField(max_length=5, default=None, blank=True, null=True)
    ProjectAchievedDate = models.DateTimeField(default=None, blank=True, null=True)
    ProjectCloseFileDate = models.DateTimeField(default=None, blank=True, null=True)
    TempProject = models.CharField(max_length=20, default=None, blank=True, null=True)
    MergeTo = models.CharField(max_length=20, default=None, blank=True, null=True)
    Note = models.CharField(max_length=500, default=None, blank=True, null=True)
    IsProjectUse = models.BooleanField(default=None, blank=True, null=True)
    SysType = models.CharField(max_length=50, default=None, blank=True, null=True)
    SiteForDept = models.CharField(max_length=10, null=True, default='')
    K_ArchiveMailDate = models.DateTimeField(default=None, blank=True, null=True)
    K_ArchiveFinishDate = models.DateTimeField(default=None, blank=True, null=True)
    K_ArchiveRemark = models.CharField(max_length=200, null=True, default='')
    BannerDesign = models.CharField(max_length=50, null=True, default='')
    DataBaseDelete = models.BooleanField(default=None, blank=True, null=True)
    EquipmentApplication = models.BooleanField(default=None, blank=True, null=True)
    ApplicationMan = models.CharField(max_length=10, null=True, default='')
    ApplicationStartDate = models.DateTimeField(default=None, blank=True, null=True)
    ApplicationDate = models.DateTimeField(default=None, blank=True, null=True)
    objects = managers.DocCollab_DBStorePath()


class DocCollab_ArchiveStorePath(models.Model):
    class Meta:
        app_label= 'PMIS'
        db_table = 'DocCollab_ArchiveStorePath'
        managed = False
    ArchiveID = models.CharField(primary_key=True, max_length=500, default='')
    Path = models.CharField(max_length=500, null=True, default='')
    Path1 = models.CharField(max_length=500, null=True, default='')
    UID = models.CharField(max_length=500, null=True, default='')


class LineGroupMapping(models.Model, method.LineGroupMapping):
    class Meta:
        app_label = 'PMIS'
        db_table = 'Line_GroupMapping'
        managed = False
    Id = models.CharField(max_length=50, primary_key=True)
    Name = models.CharField(max_length=50, null=True, default=None)
    Project = models.CharField(max_length=20, null=True, default=None)
    CreateDate = models.DateTimeField(null=True, default=None)
    objects = managers.LineGroupMapping()

class LineUser(models.Model):
    class Meta:
        app_label = 'PMIS'
        db_table = 'Line_User'
        managed = False
    UserId = models.CharField(max_length=100, primary_key=True)
    UserName = models.CharField(max_length=50, null=True, default=None)
    UserProfile = models.CharField(max_length=80, null=True, default=None)
    EditUser = models.CharField(max_length=50, null=True, default=None)
    EditDate = models.DateTimeField(null=True, default=None)

class LineMessage(models.Model, method.LineMessage):
    class Meta:
        app_label = 'PMIS'
        db_table = 'Line_Message'
        managed = False
    UID = models.CharField(max_length=50, primary_key=True)
    CreateDate = models.DateTimeField(null=True, default=None)
    SourceType = models.CharField(max_length=200, null=True, default=None)
    GroupId = models.CharField(max_length=100, null=True, default=None)
    RoomId = models.CharField(max_length=100, null=True, default=None)
    UserId = models.CharField(max_length=100, null=True, default=None)
    DisplayName = models.CharField(max_length=100, null=True, default=None)
    MsgText = models.CharField(max_length=1000, null=True, default=None)
    ImageUID = models.CharField(max_length=50, null=True, default=None)
    FileUID = models.CharField(max_length=50, null=True, default=None)
    BaseName = models.CharField(max_length=200, null=True, default=None)
    ExtName = models.CharField(max_length=20, null=True, default=None)
    CopyToProj = models.CharField(max_length=2, null=True, default=None)
    KillSource = models.BooleanField(null=True, default=None)






