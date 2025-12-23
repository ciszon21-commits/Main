from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Project, Discipline

@receiver(post_save, sender=Project)
def create_overall_discipline(sender, instance, created, **kwargs):
    """標案創建後自動創建整合專業"""
    if created:
        # 檢查是否已存在整合專業
        if not instance.disciplines.filter(is_overall=True).exists():
            Discipline.objects.create(
                project=instance,
                code='00',
                name='整合',
                is_overall=True,
                responsible_user=None  # 之後可以由管理員指定
            )

@receiver(m2m_changed, sender=Project.admins.through)
def assign_first_admin_to_overall(sender, instance, action, **kwargs):
    """當標案管理員變更時，將第一位管理員設為整合專業負責人"""
    if action in ['post_add', 'post_remove', 'post_clear']:
        overall_discipline = instance.disciplines.filter(is_overall=True).first()
        if overall_discipline:
            first_admin = instance.admins.first()
            if first_admin and overall_discipline.responsible_user != first_admin:
                overall_discipline.responsible_user = first_admin
                overall_discipline.save()
