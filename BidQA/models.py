from django.db import models
from django.contrib.auth.models import User


class Bid(models.Model):
    """標案模型"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已投標'),
        ('won', '得標'),
        ('lost', '未得標'),
        ('cancelled', '已取消'),
    ]
    
    name = models.CharField(max_length=300, verbose_name="標案名稱")
    bid_number = models.CharField(max_length=100, blank=True, verbose_name="標案編號")
    bid_date = models.DateField(null=True, blank=True, verbose_name="開標日期")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="狀態"
    )
    description = models.TextField(blank=True, verbose_name="說明")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bids_created',
        verbose_name="建立者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        verbose_name = "標案"
        verbose_name_plural = "標案"
        ordering = ['-bid_date', '-created_at']
    
    def __str__(self):
        return self.name
    
    def get_committee_count(self):
        """取得委員數量"""
        return self.bid_committees.count()
    
    def get_question_count(self):
        """取得問題總數"""
        return sum(bc.questions.count() for bc in self.bid_committees.all())


class Committee(models.Model):
    """評審委員模型"""
    name = models.CharField(max_length=100, verbose_name="委員姓名")
    organization = models.CharField(max_length=200, blank=True, verbose_name="所屬單位")
    specialty = models.CharField(max_length=200, blank=True, verbose_name="專長領域")
    notes = models.TextField(blank=True, verbose_name="備註")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    
    class Meta:
        verbose_name = "評審委員"
        verbose_name_plural = "評審委員"
        ordering = ['name']
    
    def __str__(self):
        if self.organization:
            return f"{self.name} ({self.organization})"
        return self.name
    
    def get_question_count(self):
        """取得該委員所有問題數量"""
        return Question.objects.filter(bid_committee__committee=self).count()


class BidCommittee(models.Model):
    """標案委員關聯模型"""
    bid = models.ForeignKey(
        Bid,
        on_delete=models.CASCADE,
        related_name='bid_committees',
        verbose_name="標案"
    )
    committee = models.ForeignKey(
        Committee,
        on_delete=models.CASCADE,
        related_name='bid_committees',
        verbose_name="委員"
    )
    
    class Meta:
        verbose_name = "標案委員"
        verbose_name_plural = "標案委員"
        unique_together = ['bid', 'committee']
    
    def __str__(self):
        return f"{self.bid.name} - {self.committee.name}"
    
    def get_question_count(self):
        """取得問題數量"""
        return self.questions.count()


class Question(models.Model):
    """委員提問與回答模型"""
    bid_committee = models.ForeignKey(
        BidCommittee,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="標案委員"
    )
    question = models.TextField(verbose_name="提問內容")
    answer = models.TextField(blank=True, verbose_name="回答內容")
    reference = models.TextField(blank=True, verbose_name="參考資料")
    order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        verbose_name = "問答記錄"
        verbose_name_plural = "問答記錄"
        ordering = ['order', 'created_at']
    
    def __str__(self):
        q_preview = self.question[:50] + '...' if len(self.question) > 50 else self.question
        return f"{self.bid_committee.committee.name}: {q_preview}"


class BidFile(models.Model):
    """標案文件模型"""
    bid = models.ForeignKey(
        Bid,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name="標案"
    )
    file = models.FileField(upload_to='bidqa/files/%Y/%m/', verbose_name="檔案")
    filename = models.CharField(max_length=255, verbose_name="檔案名稱")
    description = models.CharField(max_length=500, blank=True, verbose_name="說明")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bidqa_files_uploaded',
        verbose_name="上傳者"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上傳時間")
    
    class Meta:
        verbose_name = "標案文件"
        verbose_name_plural = "標案文件"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.filename
    
    def get_download_count(self):
        """取得下載次數"""
        return self.downloads.count()


class FileDownloadLog(models.Model):
    """文件下載記錄模型 - 公開紀錄"""
    file = models.ForeignKey(
        BidFile,
        on_delete=models.CASCADE,
        related_name='downloads',
        verbose_name="檔案"
    )
    downloaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bidqa_downloads',
        verbose_name="下載者"
    )
    downloaded_at = models.DateTimeField(auto_now_add=True, verbose_name="下載時間")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP 位址")
    
    class Meta:
        verbose_name = "下載記錄"
        verbose_name_plural = "下載記錄"
        ordering = ['-downloaded_at']
    
    def __str__(self):
        user_name = self.downloaded_by.get_full_name() if self.downloaded_by else '未登入'
        return f"{self.file.filename} - {user_name} - {self.downloaded_at.strftime('%Y/%m/%d %H:%M')}"

