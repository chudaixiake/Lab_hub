#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lab_hub_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
    # $env:Path = "F:\miniconda3;F:\miniconda3\Scripts;F:\miniconda3\Library\bin;" + $env:Path 
    # git push 推送到默认分支 
    # git push origin main 推送到 main 分支 
    # git push -u origin main 首次推送并设置上游 
    # git push -f 强制推送（慎用） 
    # git push --tags 推送标签 
    # git pull 拉取并合并 
    # git pull --rebase 拉取并 rebase 
    # git status 查看状态 
    # git log 查看提交历史
    # python manage.py runserver 0.0.0.0:8000
    # python manage.py runserver 0.0.0.0:8000 --insecure
