from django.contrib import admin
from .models import UserProfile, DailyPlan


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "research_topic")
    search_fields = ("user__username", "research_topic")
    list_select_related = ("user",)


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "short_content", "is_completed")
    list_filter = ("is_completed", "date", "user")
    search_fields = ("user__username", "content")
    list_editable = ("is_completed",)
    date_hierarchy = "date"

    def short_content(self, obj):
        return obj.content[:40] + ("..." if len(obj.content) > 40 else "")
    short_content.short_description = "计划内容"

    # 1) 行级权限：普通用户仅看自己的计划
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("user")
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    # 2) 新建时普通用户隐藏 user 字段，防篡改
    def get_fields(self, request, obj=None):
        fields = ["user", "date", "content", "is_completed"]
        if not request.user.is_superuser:
            fields.remove("user")
        return fields

    # 普通用户编辑已有对象时，user 只读（双保险）
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        if obj:
            return ("date",)
        return ("date",)

    # 3) 保存时自动绑定当前登录用户
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    # 对象级权限：普通用户只能改/删自己的数据
    def has_change_permission(self, request, obj=None):
        has_perm = super().has_change_permission(request, obj)
        if not has_perm or obj is None or request.user.is_superuser:
            return has_perm
        return obj.user_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        has_perm = super().has_delete_permission(request, obj)
        if not has_perm or obj is None or request.user.is_superuser:
            return has_perm
        return obj.user_id == request.user.id
