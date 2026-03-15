from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class ResumeBasicsForm(forms.Form):
    """简历基本信息表单"""
    name = forms.CharField(
        label="姓名",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入您的姓名'
        })
    )
    headline = forms.CharField(
        label="标题/职位",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '例如：软件工程师 | 全栈开发者'
        })
    )
    email = forms.EmailField(
        label="邮箱",
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    phone = forms.CharField(
        label="电话",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(123) 456-7890'
        })
    )
    location = forms.CharField(
        label="所在地",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '城市，省份'
        })
    )
    summary = forms.CharField(
        label="个人简介",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '简要描述您的专业背景和技能...'
        })
    )


class EducationForm(forms.Form):
    """教育经历表单"""
    institution = forms.CharField(
        label="学校/机构",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '学校名称'
        })
    )
    degree = forms.ChoiceField(
        label="学位",
        choices=[
            ('High School', '高中'),
            ('Associate', '专科'),
            ('Bachelor', '本科'),
            ('Master', '硕士'),
            ('Doctor', '博士'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    area = forms.CharField(
        label="专业",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '专业名称'
        })
    )
    start_date = forms.CharField(
        label="开始日期",
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYYY-MM'
        })
    )
    end_date = forms.CharField(
        label="结束日期",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYYY-MM 或留空表示至今'
        })
    )
    description = forms.CharField(
        label="描述",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '主修课程、成就等...'
        })
    )


class WorkExperienceForm(forms.Form):
    """工作经历表单"""
    company = forms.CharField(
        label="公司名称",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '公司名称'
        })
    )
    position = forms.CharField(
        label="职位",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '职位名称'
        })
    )
    start_date = forms.CharField(
        label="开始日期",
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYYY-MM'
        })
    )
    end_date = forms.CharField(
        label="结束日期",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYYY-MM 或留空表示至今'
        })
    )
    description = forms.CharField(
        label="工作描述",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '工作职责和成就...'
        })
    )


class SkillForm(forms.Form):
    """技能表单"""
    category = forms.CharField(
        label="技能类别",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '例如：编程语言、框架、工具等'
        })
    )
    skills = forms.CharField(
        label="技能列表",
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '用逗号分隔，例如：Python, Java, JavaScript'
        })
    )


class ProjectForm(forms.Form):
    """项目经历表单"""
    name = forms.CharField(
        label="项目名称",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '项目名称'
        })
    )
    description = forms.CharField(
        label="项目描述",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '项目概述、技术栈、您的贡献等...'
        })
    )
    link = forms.URLField(
        label="项目链接",
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://...'
        })
    )
