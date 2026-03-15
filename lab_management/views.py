from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django import forms
from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.db import models
import os
import json
import hmac
import hashlib
import base64
import time
from datetime import datetime
import requests
from .models import UserProfile, Document, DailyPlan, Announcement, Achievement, Message


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name']
    
    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("两次输入的密码不一致")
        return password_confirm


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
            return render(request, 'lab_management/register.html', {'form': form})
        
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            is_staff=True
        )
        
        UserProfile.objects.create(
            user=user,
            research_topic='待填写',
            bio=''
        )
        
        user = authenticate(username=username, password=password)
        login(request, user)
        messages.success(request, '注册成功！请完善您的个人资料')
        return redirect('my_page')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'lab_management/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, '用户名或密码错误')
    
    return render(request, 'lab_management/login.html')


def user_logout(request):
    logout(request)
    return redirect('home')


def home(request):
    members = UserProfile.objects.select_related('user').filter(user__is_superuser=False).all()
    recent_plans = DailyPlan.objects.select_related('user').filter(user__is_superuser=False).all()[:10]
    announcements = Announcement.objects.all()[:3]
    announcement_count = Announcement.objects.count()
    # 只统计公开文档
    document_count = Document.objects.filter(is_public=True).count()
    context = {
        'members': members,
        'recent_plans': recent_plans,
        'announcements': announcements,
        'announcement_count': announcement_count,
        'document_count': document_count,
    }
    return render(request, 'lab_management/home.html', context)


def member_list(request):
    members = UserProfile.objects.select_related('user').filter(user__is_superuser=False).all()
    context = {'members': members}
    return render(request, 'lab_management/member_list.html', context)


def plan_list(request):
    from datetime import datetime, timedelta
    import calendar as cal
    
    view = request.GET.get('view', 'list')
    plans = DailyPlan.objects.select_related('user').all()
    
    context = {
        'plans': plans,
        'view': view
    }
    
    if view == 'calendar':
        # 获取当前月份
        month_param = request.GET.get('month')
        if month_param:
            try:
                year, month = map(int, month_param.split('-'))
            except:
                today = datetime.now()
                year, month = today.year, today.month
        else:
            today = datetime.now()
            year, month = today.year, today.month
        
        # 计算上个月和下个月
        if month == 1:
            prev_month = f"{year-1}-12"
            next_month = f"{year}-2"
        elif month == 12:
            prev_month = f"{year}-{month-1}"
            next_month = f"{year+1}-1"
        else:
            prev_month = f"{year}-{month-1}"
            next_month = f"{year}-{month+1}"
        
        # 获取当月天数
        month_days = cal.monthrange(year, month)[1]
        
        # 获取当月所有计划
        month_plans = plans.filter(date__year=year, date__month=month)
        
        # 构建日历数据
        calendar_days = []
        first_day = datetime(year, month, 1).weekday()
        
        # 添加空白的起始天
        for _ in range(first_day):
            calendar_days.append({'day': '', 'plans': [], 'is_today': False})
        
        today = datetime.now()
        for day in range(1, month_days + 1):
            day_plans = month_plans.filter(date=datetime(year, month, day).date())
            calendar_days.append({
                'day': day,
                'plans': list(day_plans),
                'is_today': (today.year == year and today.month == month and today.day == day)
            })
        
        context.update({
            'year': year,
            'month': month,
            'prev_month': prev_month,
            'next_month': next_month,
            'calendar_days': calendar_days
        })
    
    return render(request, 'lab_management/plan_list.html', context)


def team_overview(request):
    members = UserProfile.objects.select_related('user').filter(user__is_superuser=False).all()
    all_plans = DailyPlan.objects.select_related('user__profile').filter(user__is_superuser=False).all().order_by('-date')
    all_achievements = Achievement.objects.filter(is_public=True, user__is_superuser=False).select_related('user__profile').all()
    
    member_data = []
    for profile in members:
        user_plans = all_plans.filter(user=profile.user)
        completed_count = user_plans.filter(is_completed=True).count()
        total_count = user_plans.count()
        
        user_documents = Document.objects.filter(user=profile.user, is_public=True)
        user_achievements = all_achievements.filter(user=profile.user)
        
        member_data.append({
            'user': profile.user,
            'profile': profile,
            'plans': user_plans[:5],
            'completed_count': completed_count,
            'total_count': total_count,
            'documents': user_documents,
            'achievements': user_achievements,
            'completion_rate': round(completed_count / total_count * 100, 0) if total_count > 0 else 0,
        })
    
    context = {
        'member_data': member_data,
        'all_plans': all_plans[:20],
        'all_achievements': all_achievements[:30],
    }
    return render(request, 'lab_management/team_overview.html', context)


def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    documents = Document.objects.filter(user=user, is_public=True)[:10]
    plans = DailyPlan.objects.filter(user=user)[:10]
    achievements = Achievement.objects.filter(user=user)[:10]
    messages_list = Message.objects.select_related('sender__profile').filter(receiver=user).order_by('-created_at')[:20]
    
    context = {
        'profile_user': user,
        'profile': profile,
        'documents': documents,
        'plans': plans,
        'achievements': achievements,
        'messages_list': messages_list,
    }
    return render(request, 'lab_management/user_profile.html', context)


def document_list(request):
    documents = Document.objects.select_related('user').filter(is_public=True)
    context = {'documents': documents}
    return render(request, 'lab_management/document_list.html', context)


def announcement_list(request):
    announcements = Announcement.objects.select_related('author').all()
    context = {'announcements': announcements}
    return render(request, 'lab_management/announcement_list.html', context)


@login_required
def my_page(request):
    user = request.user
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=user, research_topic='待填写')
        profile = user.profile
    
    documents = Document.objects.filter(user=user)
    plans = DailyPlan.objects.filter(user=user)
    achievements = Achievement.objects.filter(user=user)
    received_messages = Message.objects.select_related('sender__profile').filter(receiver=user).order_by('-created_at')[:20]
    
    # 标记收到的消息为已读
    Message.objects.filter(receiver=user, is_read=False).update(is_read=True)
    
    context = {
        'profile': profile,
        'documents': documents,
        'plans': plans,
        'achievements': achievements,
        'received_messages': received_messages,
    }
    return render(request, 'lab_management/my_page.html', context)


@login_required
def add_document(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        
        if not file:
            messages.error(request, '请选择要上传的文件')
            return redirect('my_page')
        
        ext = file.name.split('.')[-1].lower()
        doc_type = 'other'
        if ext in ['pdf']:
            doc_type = 'pdf'
        elif ext in ['doc', 'docx']:
            doc_type = 'word'
        elif ext in ['xls', 'xlsx']:
            doc_type = 'excel'
        elif ext in ['txt']:
            doc_type = 'txt'
        
        is_public = request.POST.get('is_public') == 'on'
        
        Document.objects.create(
            user=request.user,
            title=title,
            file=file,
            document_type=doc_type,
            description=description,
            is_public=is_public
        )
        
        messages.success(request, '文档上传成功！')
        return redirect('my_page')
    
    return redirect('my_page')


@login_required
def download_document(request, doc_id):
    """下载文档（强制下载而不是预览）"""
    try:
        doc = Document.objects.get(id=doc_id)
        
        # 检查权限：私密文档只有所有者或超级用户可以下载
        if not doc.is_public:
            if request.user != doc.user and not request.user.is_superuser:
                messages.error(request, '您没有权限下载此文档')
                return redirect('document_list')
        
        if not doc.file or not os.path.exists(doc.file.path):
            messages.error(request, '文件不存在或已被删除')
            return redirect('document_list')
        
        # 读取文件
        with open(doc.file.path, 'rb') as f:
            file_content = f.read()
        
        # 使用原始文件名（避免中文文件名问题）
        original_filename = doc.file.name.split('/')[-1]
        
        # 创建下载响应
        response = HttpResponse(file_content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{original_filename}"'
        response['Content-Length'] = len(file_content)
        
        return response
        
    except Document.DoesNotExist:
        messages.error(request, '文档不存在')
        return redirect('document_list')
    except Exception as e:
        messages.error(request, f'下载失败')
        return redirect('document_list')


def preview_document(request, doc_id):
    """预览文档"""
    try:
        doc = Document.objects.get(id=doc_id)
        
        # 检查权限
        if not doc.is_public:
            if not request.user.is_authenticated or (request.user != doc.user and not request.user.is_superuser):
                return HttpResponse("无权限", status=403)
        
        if not doc.file or not os.path.exists(doc.file.path):
            messages.error(request, '文件不存在或已被删除')
            return redirect('document_list')
        
        # 获取文件扩展名
        file_ext = doc.file.name.split('.')[-1].lower()
        
        # 支持预览的文件类型
        preview_types = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'txt']
        
        if file_ext in ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'pdf']:
            # Office 文档和 PDF 暂不支持预览
            html = '<html><head><meta charset="utf-8"></head><body style="font-family: sans-serif; padding: 40px; text-align: center;"><h2>暂不支持在线预览</h2><p>该文件类型暂不支持在线预览，请下载后查看</p><a href="/documents/" style="color: #2563eb;">返回文档列表</a></body></html>'
            return HttpResponse(html, content_type='text/html; charset=utf-8')
        
        if file_ext == 'txt':
            # TXT 文件直接读取内容
            try:
                with open(doc.file.path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return HttpResponse(f'<pre style="padding: 20px; font-family: monospace; white-space: pre-wrap; word-wrap: break-word;">{content}</pre>', content_type='text/html; charset=utf-8')
            except:
                return download_document(request, doc_id)
        
        # 图片文件直接显示
        if file_ext in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp']:
            file_url = doc.file.url
            html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>预览 - {doc.title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #1f2937; min-height: 100vh; }}
        .header {{
            background: rgba(0,0,0,0.5);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
        }}
        .header h1 {{ font-size: 16px; color: white; font-weight: 600; }}
        .header .actions {{ display: flex; gap: 10px; }}
        .header a {{
            padding: 6px 14px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
        }}
        .btn-primary {{ background: #6366f1; color: white; }}
        .btn-secondary {{ background: rgba(255,255,255,0.2); color: white; }}
        .preview-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 80px 20px 20px;
        }}
        .preview-container img {{
            max-width: 100%;
            max-height: calc(100vh - 100px);
            object-fit: contain;
            border-radius: 8px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🖼️ {doc.title}</h1>
        <div class="actions">
            <a href="{file_url}" download class="btn-primary">下载</a>
            <a href="/documents/" class="btn-secondary">返回</a>
        </div>
    </div>
    <div class="preview-container">
        <img src="{file_url}" alt="{doc.title}">
    </div>
</body>
</html>'''
            return HttpResponse(html, content_type='text/html; charset=utf-8')
        
        # 其他不支持预览的类型
        html = '<html><head><meta charset="utf-8"></head><body style="font-family: sans-serif; padding: 40px; text-align: center;"><h2>暂不支持在线预览</h2><p>该文件类型暂不支持在线预览，请下载后查看</p><a href="/documents/" style="color: #2563eb;">返回文档列表</a></body></html>'
        return HttpResponse(html, content_type='text/html; charset=utf-8')
        
    except Document.DoesNotExist:
        messages.error(request, '文档不存在')
        return redirect('document_list')
    except Exception as e:
        messages.error(request, f'预览失败')
        return redirect('document_list')


@login_required
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if request.user == doc.user or request.user.is_superuser:
        doc.file.delete()
        doc.delete()
        messages.success(request, '文档删除成功！')
    else:
        messages.error(request, '您没有权限删除此文档')
    return redirect('my_page')


@login_required
def add_plan(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        date = request.POST.get('date')
        
        if not content:
            messages.error(request, '请填写计划内容')
            return redirect('my_page')
        
        DailyPlan.objects.create(
            user=request.user,
            content=content,
            date=date or None
        )
        
        messages.success(request, '计划添加成功！')
        return redirect('my_page')
    
    return redirect('my_page')


@login_required
def edit_plan(request, plan_id):
    plan = get_object_or_404(DailyPlan, id=plan_id)
    
    if request.user != plan.user and not request.user.is_superuser:
        messages.error(request, '您没有权限修改此计划')
        return redirect('my_page')
    
    if request.method == 'POST':
        plan.content = request.POST.get('content')
        plan.date = request.POST.get('date') or None
        plan.is_completed = request.POST.get('is_completed') == 'on'
        plan.save()
        messages.success(request, '计划更新成功！')
        return redirect('my_page')
    
    context = {'plan': plan}
    return render(request, 'lab_management/edit_plan.html', context)


@login_required
def delete_plan(request, plan_id):
    plan = get_object_or_404(DailyPlan, id=plan_id)
    if request.user == plan.user or request.user.is_superuser:
        plan.delete()
        messages.success(request, '计划删除成功！')
    else:
        messages.error(request, '您没有权限删除此计划')
    return redirect('my_page')


@login_required
def toggle_plan(request, plan_id):
    plan = get_object_or_404(DailyPlan, id=plan_id)
    if request.user == plan.user or request.user.is_superuser:
        plan.is_completed = not plan.is_completed
        plan.save()
    return redirect('my_page')


@login_required
def add_announcement(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        is_pinned = request.user.is_superuser and request.POST.get('is_pinned') == 'on'
        
        if not title or not content:
            messages.error(request, '请填写标题和内容')
            return redirect('my_page')
        
        Announcement.objects.create(
            author=request.user,
            title=title,
            content=content,
            is_pinned=is_pinned
        )
        
        messages.success(request, '公告发布成功！')
        return redirect('announcement_list')
    
    return redirect('my_page')


@login_required
def edit_announcement(request, ann_id):
    announcement = get_object_or_404(Announcement, id=ann_id)
    
    if request.user != announcement.author and not request.user.is_superuser:
        messages.error(request, '您没有权限修改此公告')
        return redirect('my_page')
    
    if request.method == 'POST':
        announcement.title = request.POST.get('title')
        announcement.content = request.POST.get('content')
        announcement.is_pinned = request.user.is_superuser and request.POST.get('is_pinned') == 'on'
        announcement.save()
        messages.success(request, '公告更新成功！')
        return redirect('announcement_list')
    
    context = {'announcement': announcement}
    return render(request, 'lab_management/edit_announcement.html', context)


@login_required
def delete_announcement(request, ann_id):
    announcement = get_object_or_404(Announcement, id=ann_id)
    if request.user == announcement.author or request.user.is_superuser:
        announcement.delete()
        messages.success(request, '公告删除成功！')
    else:
        messages.error(request, '您没有权限删除此公告')
    return redirect('announcement_list')


@login_required
def edit_profile(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.research_topic = request.POST.get('research_topic', '')
        profile.bio = request.POST.get('bio', '')
        profile.personal_page = request.POST.get('personal_page', '')
        profile.email = request.POST.get('email', '')
        profile.phone = request.POST.get('phone', '')
        
        # 处理头像上传
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES.get('avatar')
        
        profile.save()
        
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.save()
        
        messages.success(request, '资料更新成功！')
        return redirect('my_page')
    
    return redirect('my_page')


@login_required
def add_achievement(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        achievement_type = request.POST.get('achievement_type')
        description = request.POST.get('description')
        link = request.POST.get('link')
        date = request.POST.get('date')
        is_public = request.POST.get('is_public', 'on') == 'on'
        
        achievement = Achievement.objects.create(
            user=request.user,
            title=title,
            achievement_type=achievement_type,
            description=description,
            link=link,
            date=date or None,
            is_public=is_public,
        )
        
        if request.FILES.get('file'):
            achievement.file = request.FILES.get('file')
            achievement.save()
        
        messages.success(request, '成果添加成功！')
        return redirect('my_page')
    
    return redirect('my_page')


@login_required
def delete_achievement(request, ach_id):
    achievement = get_object_or_404(Achievement, id=ach_id)
    if request.user == achievement.user or request.user.is_superuser:
        if achievement.file:
            achievement.file.delete()
        achievement.delete()
        messages.success(request, '成果已删除')
    else:
        messages.error(request, '您没有权限删除此成果')
    return redirect('my_page')


@login_required
def send_message(request, username):
    receiver = get_object_or_404(User, username=username)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                content=content,
            )
            messages.success(request, f'留言已发送给 {receiver.first_name or receiver.username}')
        else:
            messages.error(request, '留言内容不能为空')
    return redirect('user_profile', username=username)


@login_required
def delete_message(request, msg_id):
    message = get_object_or_404(Message, id=msg_id)
    if request.user == message.receiver or request.user == message.sender:
        message.delete()
        messages.success(request, '留言已删除')
    else:
        messages.error(request, '您没有权限删除此留言')
    
    if request.user == message.receiver:
        return redirect('my_page')
    else:
        return redirect('user_profile', username=message.receiver.username)


@login_required
def delete_user(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, '只有管理员可以删除用户')
        return redirect('my_page')
    
    user_to_delete = get_object_or_404(User, id=user_id)
    if user_to_delete == request.user:
        messages.error(request, '不能删除自己的账号')
        return redirect('my_page')
    
    for profile in user_to_delete.profile.documents.all():
        profile.file.delete()
    user_to_delete.delete()
    messages.success(request, '用户已删除')
    return redirect('home')


@login_required
def search(request):
    """站内搜索"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return render(request, 'lab_management/search.html', {
            'query': '',
            'results': {'members': [], 'achievements': [], 'documents': [], 'announcements': [], 'plans': []}
        })
    
    from .models import UserProfile, Achievement, Document, Announcement, DailyPlan
    
    results = {
        'members': [],
        'achievements': [],
        'documents': [],
        'announcements': [],
        'plans': []
    }
    
    # 搜索成员（用户名、姓名、研究方向）
    profiles = UserProfile.objects.select_related('user').filter(
        user__is_superuser=False
    ).filter(
        models.Q(user__username__icontains=query) |
        models.Q(user__first_name__icontains=query) |
        models.Q(research_topic__icontains=query) |
        models.Q(bio__icontains=query)
    )[:10]
    results['members'] = profiles
    
    # 搜索成果
    achievements = Achievement.objects.filter(
        models.Q(title__icontains=query) |
        models.Q(description__icontains=query) |
        models.Q(achievement_type__icontains=query)
    ).select_related('user')[:10]
    results['achievements'] = achievements
    
    # 搜索文档（只显示公开的）
    documents = Document.objects.filter(
        is_public=True
    ).filter(
        models.Q(title__icontains=query) |
        models.Q(description__icontains=query)
    ).select_related('user')[:10]
    results['documents'] = documents
    
    # 搜索公告
    announcements = Announcement.objects.filter(
        models.Q(title__icontains=query) |
        models.Q(content__icontains=query)
    ).select_related('author')[:10]
    results['announcements'] = announcements
    
    # 搜索工作计划
    plans = DailyPlan.objects.filter(
        models.Q(content__icontains=query)
    ).select_related('user')[:10]
    results['plans'] = plans
    
    return render(request, 'lab_management/search.html', {
        'query': query,
        'results': results
    })


def get_lab_data_for_ai(question):
    """根据问题获取相关的实验室数据"""
    from .models import DailyPlan, UserProfile, Achievement, Document, Announcement
    from django.contrib.auth.models import User
    from django.utils import timezone
    
    data_context = []
    question_lower = question.lower()
    
    # 检查是否询问任务/计划相关
    if any(keyword in question_lower for keyword in ['任务', '计划', '工作', '完成', '进度', 'todo']):
        plans = DailyPlan.objects.all().select_related('user__profile').order_by('-date', '-id')[:20]
        if plans:
            data_context.append("【工作计划列表】")
            completed_count = {}
            pending_count = {}
            for plan in plans:
                username = plan.user.username
                if plan.is_completed:
                    completed_count[username] = completed_count.get(username, 0) + 1
                else:
                    pending_count[username] = pending_count.get(username, 0) + 1
                status_text = "✅已完成" if plan.is_completed else "⏳进行中"
                data_context.append(f"- {plan.user.username}: {plan.content} ({status_text}, {plan.date})")
            
            if completed_count:
                data_context.append("\n【任务完成统计】")
                for username, count in sorted(completed_count.items(), key=lambda x: x[1], reverse=True):
                    data_context.append(f"- {username}: 完成 {count} 个任务")
        
    # 检查是否询问成员相关
    if any(keyword in question_lower for keyword in ['成员', '用户', '谁', '人员', '大家', '成员列表']):
        profiles = UserProfile.objects.select_related('user').filter(user__is_superuser=False)
        if profiles:
            data_context.append("【实验室成员列表】")
            for profile in profiles:
                data_context.append(f"- {profile.user.username} ({profile.user.first_name or '未设置姓名'}): {profile.research_topic}")
    
    # 检查是否询问成果相关
    if any(keyword in question_lower for keyword in ['成果', '论文', '专利', '奖项', '发表', 'achievement']):
        achievements = Achievement.objects.all().order_by('-date')[:15]
        if achievements:
            data_context.append("【实验室成果列表】")
            for ach in achievements:
                type_text = {"论文": "📄", "专利": "💡", "奖项": "🏆", "其他": "📌"}.get(ach.achievement_type, "📌")
                data_context.append(f"- {ach.user.username}: {type_text} {ach.title} ({ach.date or '日期未知'})")
    
    # 检查是否询问文档相关
    if any(keyword in question_lower for keyword in ['文档', '文件', '资料', 'document']):
        docs = Document.objects.filter(is_public=True).order_by('-uploaded_at')[:10]
        if docs:
            data_context.append("【公开文档列表】")
            for doc in docs:
                data_context.append(f"- {doc.title} (上传者: {doc.user.username}, {doc.uploaded_at.date()})")
    
    # 检查是否询问公告相关
    if any(keyword in question_lower for keyword in ['公告', '通知', 'announcement']):
        announcements = Announcement.objects.order_by('-id')[:5]
        if announcements:
            data_context.append("【最新公告】")
            for ann in announcements:
                data_context.append(f"- {ann.title}: {ann.content[:50]}...")
    
    return "\n".join(data_context) if data_context else ""


@login_required
@require_POST
def ai_chat(request):
    """AI 对话接口"""
    try:
        user_message = request.POST.get('message', '')
        if not user_message:
            return JsonResponse({'error': '消息不能为空'}, status=400)
        
        # 根据问题获取相关的实验室数据
        lab_data = get_lab_data_for_ai(user_message)
        
        # 构建系统提示，包含实验室数据
        system_prompt = """你是一个实验室助手，负责回答用户关于学习、科研、工作等方面的问题。回答要简洁明了，友好专业。

实验室数据查询说明：
- 如果用户询问任务完成情况，请根据提供的任务列表统计并分析
- 如果用户询问成员信息，请根据成员列表回答
- 如果用户询问成果，请根据成果列表回答
- 如果用户询问的问题需要数据支持，请先查看下面提供的实验室数据

"""
        if lab_data:
            system_prompt += f"\n以下是实验室的实时数据：\n{lab_data}\n"
        
        # 获取会话历史（从 session 中）
        conversation_history = request.session.get('conversation_history', [])
        
        # 构建请求体
        messages = []
        # 添加系统提示
        messages.append({
            "Role": "system",
            "Content": system_prompt
        })
        # 添加历史对话（最近 6 轮）
        for msg in conversation_history[-6:]:
            messages.append({
                "Role": msg.get("role", "user"),
                "Content": msg.get("content", "")
            })
        # 添加当前问题
        messages.append({
            "Role": "user",
            "Content": user_message
        })
        
        # 调用腾讯云 API
        response = call_tencent_ai(messages)
        
        # 调试：打印响应
        print("API 响应:", response)
        
        # 腾讯云 API 响应在 response['Response'] 中
        api_response = response.get('Response', response)
        
        if api_response and 'Choices' in api_response and len(api_response['Choices']) > 0:
            ai_reply = api_response['Choices'][0]['Message']['Content']
            
            # 更新会话历史
            conversation_history.append({
                "role": "user",
                "content": user_message
            })
            conversation_history.append({
                "role": "assistant",
                "content": ai_reply
            })
            request.session['conversation_history'] = conversation_history
            
            return JsonResponse({
                'success': True,
                'message': ai_reply
            })
        elif 'Error' in api_response:
            error_msg = api_response.get('Error', {}).get('Message', str(api_response))
            return JsonResponse({'error': 'API 错误：' + error_msg}, status=500)
        else:
            return JsonResponse({'error': 'AI 响应异常：' + str(api_response)}, status=500)
            
    except Exception as e:
        print("AI 对话错误:", str(e))
        return JsonResponse({'error': '服务器错误：' + str(e)}, status=500)


def export_data(request):
    """导出数据"""
    export_type = request.GET.get('type', 'achievements')
    
    if export_type == 'achievements':
        achievements = Achievement.objects.all().select_related('user')
        
        csv_data = "标题,类型,用户,日期,描述\n"
        for ach in achievements:
            title = ach.title.replace(',', ';').replace('\n', ' ')
            desc = (ach.description or '').replace(',', ';').replace('\n', ' ')
            csv_data += f"{title},{ach.achievement_type},{ach.user.username},{ach.date or ''},{desc}\n"
        
        filename = "achievements.csv"
        
    elif export_type == 'plans':
        plans = DailyPlan.objects.all().select_related('user')
        
        csv_data = "用户,日期,内容,状态\n"
        for plan in plans:
            content = plan.content.replace(',', ';').replace('\n', ' ')
            status = "已完成" if plan.is_completed else "进行中"
            csv_data += f"{plan.user.username},{plan.date},{content},{status}\n"
        
        filename = "plans.csv"
        
    elif export_type == 'members':
        profiles = UserProfile.objects.select_related('user').filter(user__is_superuser=False)
        
        csv_data = "用户名,姓名,研究方向,邮箱,电话\n"
        for profile in profiles:
            name = profile.user.first_name or ''
            topic = (profile.research_topic or '').replace(',', ';')
            email = profile.email or ''
            phone = profile.phone or ''
            csv_data += f"{profile.user.username},{name},{topic},{email},{phone}\n"
        
        filename = "members.csv"
    else:
        return HttpResponse("无效的导出类型")
    
    response = HttpResponse(csv_data.encode('utf-8-sig'), content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def resume_builder(request):
    """简历生成器"""
    from .forms import ResumeBasicsForm, EducationForm, WorkExperienceForm, SkillForm, ProjectForm
    
    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        
        if action == 'generate_pdf':
            # 收集表单数据
            resume_data = {
                'basics': {
                    'name': request.POST.get('name', ''),
                    'headline': request.POST.get('headline', ''),
                    'email': request.POST.get('email', ''),
                    'phone': request.POST.get('phone', ''),
                    'location': request.POST.get('location', ''),
                    'summary': request.POST.get('summary', ''),
                    'photo': request.POST.get('photo_data', ''),  # 获取照片数据
                },
                'education': [],
                'work': [],
                'skills': [],
                'projects': [],
            }
            
            # 调试信息
            print(f"收到照片数据：{'有' if resume_data['basics']['photo'] else '无'}")
            if resume_data['basics']['photo']:
                print(f"照片数据长度：{len(resume_data['basics']['photo'])}")
                print(f"照片数据前缀：{resume_data['basics']['photo'][:50]}...")
            
            # 处理教育经历
            edu_count = int(request.POST.get('education_count', 0))
            for i in range(edu_count):
                prefix = f'education_{i}'
                edu = {
                    'institution': request.POST.get(f'{prefix}_institution', ''),
                    'degree': request.POST.get(f'{prefix}_degree', ''),
                    'area': request.POST.get(f'{prefix}_area', ''),
                    'start_date': request.POST.get(f'{prefix}_start_date', ''),
                    'end_date': request.POST.get(f'{prefix}_end_date', ''),
                    'description': request.POST.get(f'{prefix}_description', ''),
                }
                if edu['institution']:
                    resume_data['education'].append(edu)
            
            # 处理工作经历
            work_count = int(request.POST.get('work_count', 0))
            for i in range(work_count):
                prefix = f'work_{i}'
                work = {
                    'company': request.POST.get(f'{prefix}_company', ''),
                    'position': request.POST.get(f'{prefix}_position', ''),
                    'start_date': request.POST.get(f'{prefix}_start_date', ''),
                    'end_date': request.POST.get(f'{prefix}_end_date', ''),
                    'description': request.POST.get(f'{prefix}_description', ''),
                }
                if work['company']:
                    resume_data['work'].append(work)
            
            # 处理技能
            skill_count = int(request.POST.get('skill_count', 0))
            for i in range(skill_count):
                prefix = f'skill_{i}'
                skill = {
                    'category': request.POST.get(f'{prefix}_category', ''),
                    'skills': request.POST.get(f'{prefix}_skills', ''),
                }
                if skill['category']:
                    resume_data['skills'].append(skill)
            
            # 处理项目
            project_count = int(request.POST.get('project_count', 0))
            for i in range(project_count):
                prefix = f'project_{i}'
                project = {
                    'name': request.POST.get(f'{prefix}_name', ''),
                    'description': request.POST.get(f'{prefix}_description', ''),
                    'link': request.POST.get(f'{prefix}_link', ''),
                }
                if project['name']:
                    resume_data['projects'].append(project)
            
            # 生成 PDF - 与前端预览布局完全一致
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import mm, cm
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                from io import BytesIO
                
                # 创建 PDF - 使用较小的边距以确保内容在一页内
                # A4 尺寸: 210mm x 297mm
                buffer = BytesIO()
                margin = 15*mm  # 减小边距以容纳更多内容
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=A4,
                    rightMargin=margin,
                    leftMargin=margin,
                    topMargin=margin,
                    bottomMargin=margin,
                )
                
                # 可用内容宽度 = A4 宽度 (210mm) - 左右边距 (15mm*2) = 180mm
                content_width = 180*mm
                
                elements = []
                styles = getSampleStyleSheet()
                
                # 注册中文字体 - 与预览 CSS 中的 SimSun 一致
                font_name = 'SimSun'
                font_name_bold = 'SimSun'
                font_registered = False
                font_paths = [
                    'C:/Windows/Fonts/simsun.ttc',
                    'C:/Windows/Fonts/SimSun.ttf',
                    '/usr/share/fonts/truetype/SimSun.ttf',
                ]
                for fp in font_paths:
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, fp))
                        font_registered = True
                        break
                    except:
                        continue
                
                if not font_registered:
                    font_name = 'Helvetica'
                    font_name_bold = 'Helvetica-Bold'
                
                # ===== 样式定义 - 与预览 CSS 像素级对应 =====
                
                # 姓名 - 对应 .resume-name: font-size:26px, font-weight:700, color:#0f172a
                title_style = ParagraphStyle(
                    'ResumeTitle',
                    parent=styles['Normal'],
                    fontSize=26,
                    textColor=colors.HexColor('#0f172a'),
                    fontName=font_name_bold if not font_registered else font_name,
                    alignment=1,
                    leading=34,
                    spaceAfter=4,
                )
                
                # 职位 - 对应 .resume-headline: font-size:14px, color:#64748b
                headline_style = ParagraphStyle(
                    'ResumeHeadline',
                    parent=styles['Normal'],
                    fontSize=14,
                    textColor=colors.HexColor('#64748b'),
                    fontName=font_name,
                    alignment=1,
                    leading=18,
                    spaceAfter=4,
                )
                
                # 联系信息 - 对应 .resume-contact: font-size:10px, color:#64748b
                contact_style = ParagraphStyle(
                    'ResumeContact',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#64748b'),
                    fontName=font_name,
                    alignment=1,
                    leading=14,
                    spaceBefore=8,
                    spaceAfter=0,
                )
                
                # 章节标题 - 对应 .resume-section-title: font-size:16px, font-weight:700, color:#0f172a
                section_title_style = ParagraphStyle(
                    'ResumeSectionTitle',
                    parent=styles['Normal'],
                    fontSize=16,
                    textColor=colors.HexColor('#0f172a'),
                    fontName=font_name_bold if not font_registered else font_name,
                    leading=20,
                    spaceBefore=10,  # 减小章节间距
                    spaceAfter=2,
                )
                
                # 条目标题 - 对应 .resume-entry-title: font-size:11px, font-weight:700, color:#0f172a
                entry_title_style = ParagraphStyle(
                    'ResumeEntryTitle',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.HexColor('#0f172a'),
                    fontName=font_name_bold if not font_registered else font_name,
                    leading=14,
                )
                
                # 条目日期 - 对应 .resume-entry-date: font-size:10px, color:#64748b, italic
                entry_date_style = ParagraphStyle(
                    'ResumeEntryDate',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#64748b'),
                    fontName=font_name,
                    leading=14,
                    alignment=2,  # 右对齐
                )
                
                # 条目副标题 - 对应 .resume-entry-subtitle: font-size:10px, color:#64748b, italic
                entry_subtitle_style = ParagraphStyle(
                    'ResumeEntrySubtitle',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#64748b'),
                    fontName=font_name,
                    leading=14,
                    spaceAfter=4,
                )
                
                # 正文/描述 - 对应 .resume-entry-description / .resume-summary-text: font-size:10px, color:#475569
                body_style = ParagraphStyle(
                    'ResumeBody',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#475569'),
                    fontName=font_name,
                    leading=14,  # 减小行高
                )
                
                # ===== 辅助函数 =====
                def add_section_divider():
                    """添加章节分隔线 - 对应 CSS border-bottom: 2px solid #e2e8f0"""
                    elements.append(HRFlowable(
                        width="100%",
                        thickness=2,
                        color=colors.HexColor('#e2e8f0'),
                        spaceBefore=0,
                        spaceAfter=6,
                    ))
                
                def add_entry_header(title_text, date_text=''):
                    """添加条目头部 - 左侧标题+右侧日期，对应预览中的 flex 布局"""
                    if date_text:
                        header_table = Table(
                            [[Paragraph(f'<b>{title_text}</b>', entry_title_style),
                              Paragraph(f'<i>{date_text}</i>', entry_date_style)]],
                            colWidths=[content_width * 0.7, content_width * 0.3],
                        )
                        header_table.setStyle(TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('TOPPADDING', (0, 0), (-1, -1), 0),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                            ('LEFTPADDING', (0, 0), (-1, -1), 0),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                        ]))
                        elements.append(header_table)
                    else:
                        elements.append(Paragraph(f'<b>{title_text}</b>', entry_title_style))
                
                # ===== 构建 PDF 内容 =====
                basics = resume_data['basics']
                
                # 先构建联系信息列表（无论是否有照片都需要）
                contact_parts = []
                if basics['email']:
                    contact_parts.append(basics['email'])
                if basics['phone']:
                    contact_parts.append(basics['phone'])
                if basics['location']:
                    contact_parts.append(basics['location'])
                contact_text = " | ".join(contact_parts) if contact_parts else ""
                
                # 处理照片（如果有）
                photo_img_element = None
                if basics.get('photo'):
                    try:
                        from reportlab.platypus import Image
                        from reportlab.lib.utils import ImageReader
                        import base64
                        from io import BytesIO
                        # 解析 base64 照片数据
                        photo_data = basics['photo']
                        if photo_data.startswith('data:image'):
                            # 移除 data:image/xxx;base64, 前缀
                            img_data = photo_data.split(',')[1]
                            img_bytes = base64.b64decode(img_data)
                            # 使用 BytesIO 创建文件-like 对象
                            img_buffer = BytesIO(img_bytes)
                            photo_img_element = Image(img_buffer)
                            print(f"照片处理成功，大小: {len(img_bytes)} bytes")
                    except Exception as e:
                        print(f"处理照片失败：{e}")
                        import traceback
                        print(traceback.format_exc())
                
                # 基本信息区域（带照片）
                if photo_img_element:
                    # 使用表格布局：左侧信息，右侧照片
                    from reportlab.platypus import Table
                    photo_width = 25*mm  # 80px ≈ 25mm
                    photo_height = 31*mm  # 100px ≈ 31mm
                    
                    # 设置图片尺寸
                    photo_img_element.drawWidth = photo_width
                    photo_img_element.drawHeight = photo_height
                    
                    # 创建左侧信息文本（将多个段落合并为一个）
                    left_text = ""
                    if basics['name']:
                        left_text += f"<font size='26' color='#0f172a'><b>{basics['name']}</b></font><br/>"
                    if basics['headline']:
                        left_text += f"<font size='14' color='#64748b'>{basics['headline']}</font><br/>"
                    if contact_text:
                        left_text += f"<font size='10' color='#64748b'>{contact_text}</font>"
                    
                    # 构建表格数据 - 左侧是段落，右侧是图片
                    left_para = Paragraph(left_text, ParagraphStyle(
                        'LeftInfo',
                        parent=styles['Normal'],
                        fontName=font_name,
                        leading=18,
                        alignment=0,  # 左对齐
                    ))
                    
                    table_data = [[left_para, photo_img_element]]
                    
                    info_table = Table(
                        table_data,
                        colWidths=[content_width - photo_width - 5*mm, photo_width],
                        rowHeights=[photo_height]
                    )
                    info_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                        ('LEFTPADDING', (0, 0), (0, 0), 0),
                        ('RIGHTPADDING', (0, 0), (0, 0), 5*mm),
                        ('LEFTPADDING', (1, 0), (1, 0), 5*mm),
                        ('RIGHTPADDING', (1, 0), (1, 0), 0),
                    ]))
                    elements.append(info_table)
                else:
                    # 没有照片，正常布局
                    # 姓名
                    if basics['name']:
                        elements.append(Paragraph(basics['name'], title_style))
                    
                    # 职位/头衔
                    if basics['headline']:
                        elements.append(Paragraph(basics['headline'], headline_style))
                    
                    # 联系信息 - 与预览一致使用 | 分隔
                    if contact_parts:
                        elements.append(Paragraph(" | ".join(contact_parts), contact_style))
                
                # 头部分隔线 - 对应 .resume-header 的 border-bottom
                elements.append(Spacer(1, 8))
                elements.append(HRFlowable(
                    width="100%",
                    thickness=2,
                    color=colors.HexColor('#e2e8f0'),
                    spaceBefore=0,
                    spaceAfter=16,
                ))
                
                # 个人简介 - 对应预览中的"个人简介"章节
                if basics['summary']:
                    elements.append(Paragraph("个人简介", section_title_style))
                    add_section_divider()
                    elements.append(Paragraph(basics['summary'], body_style))
                
                # 教育经历
                if resume_data['education']:
                    elements.append(Paragraph("教育经历", section_title_style))
                    add_section_divider()
                    
                    for edu in resume_data['education']:
                        # 日期字符串
                        date_str = ''
                        if edu['start_date'] and edu['end_date']:
                            date_str = f"{edu['start_date']} - {edu['end_date']}"
                        elif edu['start_date']:
                            date_str = f"{edu['start_date']} - 至今"
                        
                        add_entry_header(edu['institution'], date_str)
                        
                        # 副标题: 学位 - 专业
                        subtitle = f"{edu['degree']} - {edu['area']}"
                        elements.append(Paragraph(f'<i>{subtitle}</i>', entry_subtitle_style))
                        
                        if edu['description']:
                            elements.append(Paragraph(edu['description'], body_style))
                        
                        elements.append(Spacer(1, 6))
                
                # 工作经历
                if resume_data['work']:
                    elements.append(Paragraph("工作经历", section_title_style))
                    add_section_divider()
                    
                    for work in resume_data['work']:
                        date_str = ''
                        if work['start_date'] and work['end_date']:
                            date_str = f"{work['start_date']} - {work['end_date']}"
                        elif work['start_date']:
                            date_str = f"{work['start_date']} - 至今"
                        
                        add_entry_header(work['company'], date_str)
                        elements.append(Paragraph(f"<i>{work['position']}</i>", entry_subtitle_style))
                        
                        if work['description']:
                            elements.append(Paragraph(work['description'], body_style))
                        
                        elements.append(Spacer(1, 6))
                
                # 技能
                if resume_data['skills']:
                    elements.append(Paragraph("技能", section_title_style))
                    add_section_divider()
                    
                    for skill in resume_data['skills']:
                        skill_text = f"<b>{skill['category']}:</b> {skill['skills']}"
                        elements.append(Paragraph(skill_text, body_style))
                        elements.append(Spacer(1, 3))
                
                # 项目经历
                if resume_data['projects']:
                    elements.append(Paragraph("项目经历", section_title_style))
                    add_section_divider()
                    
                    for project in resume_data['projects']:
                        project_title = project['name']
                        if project['link']:
                            project_title += f" ({project['link']})"
                        
                        elements.append(Paragraph(f'<b>{project_title}</b>', entry_title_style))
                        
                        if project['description']:
                            elements.append(Paragraph(project['description'], body_style))
                        
                        elements.append(Spacer(1, 6))
                
                # 构建 PDF
                doc.build(elements)
                buffer.seek(0)
                
                response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                filename = f"{basics['name'].replace(' ', '_')}_简历.pdf" if basics['name'] else "resume.pdf"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                # 禁用缓存以确保每次下载都是最新的
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
                
            except Exception as e:
                import traceback
                error_msg = f'生成 PDF 失败：{str(e)}'
                print(f"PDF 生成错误：{traceback.format_exc()}")
                
                # 检查是否是 AJAX 请求
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'error': error_msg}, status=500)
                else:
                    messages.error(request, error_msg)
                    return redirect('resume_builder')
    
    # GET 请求，显示表单
    context = {
        'basics_form': ResumeBasicsForm(),
        'education_form': EducationForm(),
        'work_form': WorkExperienceForm(),
        'skill_form': SkillForm(),
        'project_form': ProjectForm(),
    }
    return render(request, 'lab_management/resume_builder.html', context)


def call_tencent_ai(messages):
    """调用腾讯云混元大模型 API"""
    import time
    import hashlib
    import hmac
    from datetime import datetime
    import json
    
    # 腾讯云 API 配置
    secret_id = settings.TENCENT_AI_SECRET_ID
    secret_key = settings.TENCENT_AI_SECRET_KEY
    service = "hunyuan"
    host = "hunyuan.tencentcloudapi.com"
    action = "ChatCompletions"
    version = "2023-09-01"
    region = "ap-guangzhou"
    model = settings.TENCENT_AI_MODEL
    
    # 构建请求体
    payload = {
        "Model": model,
        "Messages": messages
    }
    
    # 准备签名
    timestamp = int(time.time())
    date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
    
    # 构建规范请求
    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    canonical_headers = "content-type:%s\nhost:%s\n" % (ct, host)
    signed_headers = "content-type;host"
    hashed_request_payload = hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode('utf-8')).hexdigest()
    canonical_request = (http_request_method + "\n" +
                         canonical_uri + "\n" +
                         canonical_querystring + "\n" +
                         canonical_headers + "\n" +
                         signed_headers + "\n" +
                         hashed_request_payload)
    
    # 构建待签名字符串
    algorithm = "TC3-HMAC-SHA256"
    credential_scope = date + "/" + service + "/" + "tc3_request"
    hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    string_to_sign = (algorithm + "\n" +
                      str(timestamp) + "\n" +
                      credential_scope + "\n" +
                      hashed_canonical_request)
    
    # 计算签名
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    secret_date = sign(("TC3" + secret_key).encode('utf-8'), date)
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # 构建授权头
    authorization = (algorithm + " " +
                     "Credential=" + secret_id + "/" + credential_scope + ", " +
                     "SignedHeaders=" + signed_headers + ", " +
                     "Signature=" + signature)
    
    # 发送请求
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Version": version,
        "X-TC-Region": region,
        "X-TC-Timestamp": str(timestamp),
        "Authorization": authorization
    }
    
    print("正在调用腾讯云 API...")
    print("请求头:", {k: v[:50] + "..." if len(str(v)) > 50 else v for k, v in headers.items()})
    print("请求体:", json.dumps(payload, ensure_ascii=False)[:200])
    
    try:
        response = requests.post(
            "https://" + host,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            timeout=30
        )
        print("HTTP 状态码:", response.status_code)
        print("响应内容:", response.text[:500])
        return response.json()
    except Exception as e:
        print("API 调用异常:", str(e))
        raise Exception(f"API 调用失败：{str(e)}")

