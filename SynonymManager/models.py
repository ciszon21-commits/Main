from django.db import models
from django.contrib.auth.models import User

class Keyword(models.Model):
    """
    關鍵字模型 (用於搜尋引擎的關鍵字清單)
    """
    word = models.CharField(max_length=255, unique=True, verbose_name="關鍵字")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="建立者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return self.word

    class Meta:
        verbose_name = "關鍵字"
        verbose_name_plural = "關鍵字"
        ordering = ['-created_at']

class SynonymGroup(models.Model):
    """
    同義詞群組模型
    """
    word = models.CharField(max_length=255, verbose_name="主詞彙", help_text="請輸入主要詞彙")
    synonym_list = models.TextField(verbose_name="同義詞列表", help_text="請輸入同義詞，以逗號 (,) 分隔")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="建立者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    def __str__(self):
        return f"{self.word} ({self.creator.username if self.creator else 'Unknown'})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 自動同步至關鍵字清單
        words_to_sync = [self.word.strip()]
        if self.synonym_list:
            words_to_sync.extend([s.strip() for s in self.synonym_list.split(',') if s.strip()])
        
        for w in words_to_sync:
            if w:
                Keyword.objects.get_or_create(
                    word=w,
                    defaults={'creator': self.creator}
                )

    class Meta:
        verbose_name = "同義詞群組"
        verbose_name_plural = "同義詞群組"
        ordering = ['-updated_at']

    @property
    def synonym_count(self):
        if not self.synonym_list:
            return 0
        return len([s for s in self.synonym_list.split(',') if s.strip()])
