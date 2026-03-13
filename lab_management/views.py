from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django import forms
from django.conf import settings
from django.http import FileResponse, HttpResponse
import os
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
    announcements = Announcement.objects.all()[:5]
    context = {
        'members': members,
        'recent_plans': recent_plans,
        'announcements': announcements,
    }
    return render(request, 'lab_management/home.html', context)


def member_list(request):
    members = UserProfile.objects.select_related('user').filter(user__is_superuser=False).all()
    context = {'members': members}
    return render(request, 'lab_management/member_list.html', context)


def plan_list(request):
    plans = DailyPlan.objects.select_related('user').all()
    context = {'plans': plans}
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
