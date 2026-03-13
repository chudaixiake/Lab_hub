from django.conf import settings
from django.db import models
from django.utils import timezone
import os


def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.user.username}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    return f'documents/{instance.user.username}/{filename}'


def avatar_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"avatar_{instance.user.username}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    return f'avatars/{instance.user.username}/{filename}'


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="组员",
    )
    research_topic = models.CharField("研究课题", max_length=120)
    bio = models.TextField("个人简介", blank=True)
    avatar = models.ImageField("头像", upload_to=avatar_directory_path, blank=True, null=True, help_text="上传本地头像图片")
    personal_page = models.URLField("个人主页链接", blank=True, help_text="个人博客、GitHub 等")
    can_post_announcement = models.BooleanField("可发布公告", default=False)

    class Meta:
        verbose_name = "个人简介"
        verbose_name_plural = "个人简介"

    def __str__(self):
        return f"{self.user.username} - {self.research_topic}"


class Document(models.Model):
    DOCUMENT_TYPES = [
        ('pdf', 'PDF'),
        ('word', 'Word'),
        ('txt', '文本'),
        ('excel', 'Excel'),
        ('other', '其他'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="上传者",
    )
    title = models.CharField("文档标题", max_length=200)
    file = models.FileField("文件", upload_to=user_directory_path)
    document_type = models.CharField("文档类型", max_length=20, choices=DOCUMENT_TYPES)
    description = models.TextField("描述", blank=True)
    is_public = models.BooleanField("公开", default=True, help_text="公开文档可被所有人查看，不公开仅自己可见")
    uploaded_at = models.DateTimeField("上传时间", auto_now_add=True)
    
    class Meta:
        verbose_name = "文档"
        verbose_name_plural = "文档"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def get_file_ext(self):
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''
    
    def is_pdf(self):
        return self.get_file_ext() in ['.pdf']
    
    def is_word(self):
        return self.get_file_ext() in ['.doc', '.docx']
    
    def is_excel(self):
        return self.get_file_ext() in ['.xls', '.xlsx']
    
    def is_txt(self):
        return self.get_file_ext() in ['.txt']


class DailyPlan(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_plans",
        verbose_name="组员",
    )
    date = models.DateField("日期", default=timezone.localdate)
    content = models.TextField("计划内容")
    is_completed = models.BooleanField("是否完成", default=False)

    class Meta:
        verbose_name = "日常计划"
        verbose_name_plural = "日常计划"
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.user.username} | {self.date} | {'已完成' if self.is_completed else '未完成'}"


class Announcement(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="announcements",
        verbose_name="发布者",
    )
    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容")
    is_pinned = models.BooleanField("置顶", default=False)

    class Meta:
        verbose_name = "公告"
        verbose_name_plural = "公告"

    def __str__(self):
        return self.title


class Achievement(models.Model):
    ACHIEVEMENT_TYPES = [
        ('paper', '论文'),
        ('patent', '专利'),
        ('award', '奖项'),
        ('project', '项目'),
        ('other', '其他'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="achievements",
        verbose_name="成员",
    )
    title = models.CharField("成果名称", max_length=300)
    achievement_type = models.CharField("类型", max_length=20, choices=ACHIEVEMENT_TYPES)
    description = models.TextField("描述", blank=True)
    file = models.FileField("附件", upload_to=user_directory_path, blank=True, null=True)
    link = models.URLField("链接", blank=True, help_text="论文链接、专利链接等")
    date = models.DateField("日期", blank=True, null=True)
    is_public = models.BooleanField("公开", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    
    class Meta:
        verbose_name = "成果"
        verbose_name_plural = "成果"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name="发送者",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_messages",
        verbose_name="接收者",
    )
    content = models.TextField("留言内容", max_length=1000)
    created_at = models.DateTimeField("留言时间", auto_now_add=True)
    is_read = models.BooleanField("已读", default=False)
    
    class Meta:
        verbose_name = "留言"
        verbose_name_plural = "留言"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username} | {self.created_at.strftime('%Y-%m-%d %H:%M')}"
