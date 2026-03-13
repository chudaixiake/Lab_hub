from django.contrib import admin
from .models import UserProfile, Document, DailyPlan, Announcement


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "research_topic", "can_post_announcement")
    list_editable = ("can_post_announcement",)
    search_fields = ("user__username", "research_topic")
    list_select_related = ("user",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "document_type", "uploaded_at")
    list_filter = ("document_type", "uploaded_at", "user")
    search_fields = ("title", "user__username", "description")
    date_hierarchy = "uploaded_at"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("user")
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile') and request.user.profile.can_post_announcement:
            return qs
        return qs.filter(user=request.user)

    def get_fields(self, request, obj=None):
        fields = ["user", "title", "file", "document_type", "description"]
        if not request.user.is_superuser:
            fields.remove("user")
        return fields

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        if obj:
            return ("uploaded_at",)
        return ()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.user = request.user
        super().save_model(request, obj, form, change)

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

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("user")
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def get_fields(self, request, obj=None):
        fields = ["user", "date", "content", "is_completed"]
        if not request.user.is_superuser:
            fields.remove("user")
        return fields

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        if obj:
            return ()
        return ()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.user = request.user
        super().save_model(request, obj, form, change)

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


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "is_pinned")
    list_editable = ("is_pinned",)
    list_filter = ("is_pinned", "author")
    search_fields = ("title", "content", "author__username")

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("author")
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile') and request.user.profile.can_post_announcement:
            return qs
        return qs.filter(author=request.user)

    def get_fields(self, request, obj=None):
        fields = ["author", "title", "content", "is_pinned"]
        if not request.user.is_superuser:
            fields.remove("author")
        return fields

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        has_perm = super().has_change_permission(request, obj)
        if not has_perm or obj is None or request.user.is_superuser:
            return has_perm
        return obj.author_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        has_perm = super().has_delete_permission(request, obj)
        if not has_perm or obj is None or request.user.is_superuser:
            return has_perm
        return obj.author_id == request.user.id
