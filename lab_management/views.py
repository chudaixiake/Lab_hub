from django.shortcuts import render
from django.contrib.auth.models import User
from .models import UserProfile, DailyPlan


def home(request):
    """实验室主页"""
    members = UserProfile.objects.select_related('user').all()
    recent_plans = DailyPlan.objects.select_related('user').all()[:10]
    context = {
        'members': members,
        'recent_plans': recent_plans,
    }
    return render(request, 'lab_management/home.html', context)


def member_list(request):
    """成员列表页面"""
    members = UserProfile.objects.select_related('user').all()
    context = {
        'members': members,
    }
    return render(request, 'lab_management/member_list.html', context)


def plan_list(request):
    """计划列表页面"""
    plans = DailyPlan.objects.select_related('user').all()
    context = {
        'plans': plans,
    }
    return render(request, 'lab_management/plan_list.html', context)
