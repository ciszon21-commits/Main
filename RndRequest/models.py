from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field


class RndRequest(models.Model):
    """許願池願望模型"""
    
    PRIORITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '提案中'),
        ('reviewing', '審核中'),
        ('accepted', '已採納'),
        ('rejected', '已拒絕'),
    ]
    
    # 基本資訊
    title = models.CharField(
        max_length=200, 
        verbose_name="願望主題",
        help_text="請簡潔描述您的願望主題"
    )
    
    # 必填欄位
    demand_quantity = models.TextField(
        verbose_name="使用量/影響範圍",
        help_text="請說明每周使用幾小時、影響人數等資訊"
    )
    data_source = models.TextField(
        verbose_name="現況說明",
        help_text="請說明目前狀況是什麼、問題來自於哪裡"
    )
    processing_flow = CKEditor5Field(
        verbose_name="處理流程",
        help_text="請提供完整的使用流程說明",
        config_name='extends'
    )
    
    # 建議欄位
    expected_outcome = models.TextField(
        verbose_name="預期效益",
        blank=True,
        help_text="若實作此需求會帶來什麼好處"
    )
    priority_level = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="緊迫程度"
    )
    
    # 狀態管理
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="狀態"
    )
    
    # 提案人與時間
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rnd_requests',
        verbose_name="提案人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        verbose_name = "願望"
        verbose_name_plural = "願望"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def vote_score(self):
        """取得淨票數"""
        return self.votes.aggregate(
            score=models.Sum('vote_type')
        )['score'] or 0
    
    @property
    def upvote_count(self):
        """取得贊成票數"""
        return self.votes.filter(vote_type=1).count()
    
    @property
    def downvote_count(self):
        """取得反對票數"""
        return self.votes.filter(vote_type=-1).count()


class RndRequestVote(models.Model):
    """投票記錄模型"""
    
    VOTE_TYPE_CHOICES = [
        (1, '贊成'),
        (-1, '反對'),
    ]
    
    request = models.ForeignKey(
        RndRequest,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name="需求"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rnd_votes',
        verbose_name="投票者"
    )
    vote_type = models.SmallIntegerField(
        choices=VOTE_TYPE_CHOICES,
        verbose_name="投票類型"
    )
    voted_at = models.DateTimeField(auto_now_add=True, verbose_name="投票時間")
    
    class Meta:
        verbose_name = "投票記錄"
        verbose_name_plural = "投票記錄"
        unique_together = ['request', 'user']  # 確保一人一票
        ordering = ['-voted_at']
    
    def __str__(self):
        vote_str = "贊成" if self.vote_type == 1 else "反對"
        return f"{self.user.get_full_name() or self.user.username} - {vote_str} - {self.request.title}"


class RndRequestComment(models.Model):
    """留言記錄模型"""
    
    request = models.ForeignKey(
        RndRequest,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="需求"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rnd_comments',
        verbose_name="留言者"
    )
    content = models.TextField(
        verbose_name="留言內容",
        help_text="請輸入您的意見或建議"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="留言時間")
    
    class Meta:
        verbose_name = "留言記錄"
        verbose_name_plural = "留言記錄"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.request.title[:20]}"
