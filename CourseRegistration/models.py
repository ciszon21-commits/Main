from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.urls import reverse


class Course(models.Model):
    """課程模型"""
    title = models.CharField(max_length=200, verbose_name='課程標題')
    description = models.TextField(verbose_name='課程說明')
    
    # 時間設定
    course_datetime = models.DateTimeField(verbose_name='上課時間')
    registration_start = models.DateTimeField(verbose_name='報名開始時間')
    registration_end = models.DateTimeField(verbose_name='報名截止時間')
    
    # PDF 附件
    pdf_file = models.FileField(
        upload_to='courses/pdfs/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='PDF 附件'
    )
    
    # 人數限制（可選）
    max_participants = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        verbose_name='報名人數上限',
        help_text='留空表示不限制人數'
    )
    
    # 課程資訊（可選）
    instructor_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='講師姓名',
        help_text='選填，可事後編輯'
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='課程地點',
        help_text='選填，可事後編輯'
    )
    
    # 建立者與時間戳記
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_courses',
        verbose_name='建立者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        verbose_name = '課程'
        verbose_name_plural = '課程'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('courses:course_detail', kwargs={'pk': self.pk})
    
    @property
    def current_participants_count(self):
        """目前報名人數"""
        return self.registrations.count()
    
    @property
    def is_registration_open(self):
        """報名是否開放中"""
        now = timezone.now()
        return self.registration_start <= now <= self.registration_end
    
    @property
    def is_full(self):
        """是否已額滿"""
        if self.max_participants is None:
            return False
        return self.current_participants_count >= self.max_participants
    
    @property
    def can_register(self):
        """是否可以報名"""
        return self.is_registration_open and not self.is_full
    
    @property
    def registration_status(self):
        """報名狀態"""
        now = timezone.now()
        if now < self.registration_start:
            return 'upcoming'  # 尚未開始
        elif now > self.registration_end:
            return 'closed'  # 已結束
        elif self.is_full:
            return 'full'  # 已額滿
        else:
            return 'open'  # 開放中
    
    @property
    def pdf_download_count(self):
        """PDF 下載次數"""
        return self.pdf_downloads.count()
    
    def clean(self):
        """表單驗證"""
        from django.core.exceptions import ValidationError
        
        if self.registration_end <= self.registration_start:
            raise ValidationError('報名截止時間必須晚於報名開始時間')
        
        if self.course_datetime <= self.registration_start:
            raise ValidationError('上課時間應該晚於報名開始時間')


class Registration(models.Model):
    """報名記錄模型"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name='課程'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='course_registrations',
        verbose_name='報名者'
    )
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='報名時間')
    
    class Meta:
        verbose_name = '報名記錄'
        verbose_name_plural = '報名記錄'
        unique_together = [['course', 'user']]
        ordering = ['registered_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.course.title}'


class PDFDownloadLog(models.Model):
    """PDF 下載記錄模型"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='pdf_downloads',
        verbose_name='課程'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pdf_downloads',
        verbose_name='下載者'
    )
    downloaded_at = models.DateTimeField(auto_now_add=True, verbose_name='下載時間')
    
    class Meta:
        verbose_name = 'PDF 下載記錄'
        verbose_name_plural = 'PDF 下載記錄'
        ordering = ['-downloaded_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.course.title} - {self.downloaded_at.strftime("%Y-%m-%d %H:%M")}'


class CourseComment(models.Model):
    """課程留言模型"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='課程'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='course_comments',
        verbose_name='留言者'
    )
    content = models.TextField(verbose_name='留言內容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='留言時間')
    
    class Meta:
        verbose_name = '課程留言'
        verbose_name_plural = '課程留言'
        ordering = ['-created_at']  # 新到舊排序
    
    def __str__(self):
        return f'{self.user.username} - {self.course.title} - {self.created_at.strftime("%Y-%m-%d %H:%M")}'
