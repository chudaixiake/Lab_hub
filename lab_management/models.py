from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="组员",
    )
    research_topic = models.CharField("研究课题", max_length=120)
    bio = models.TextField("个人简介", blank=True)

    class Meta:
        verbose_name = "个人简介"
        verbose_name_plural = "个人简介"

    def __str__(self):
        return f"{self.user.username} - {self.research_topic}"


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
