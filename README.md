# 实验室管理系统 (Lab Hub)

基于 Django 5 构建的实验室管理平台，用于管理实验室成员、工作计划、科研成果、文档资料和公告通知。

## 功能特性

###  成员管理
- 用户注册、登录、退出
- 个人资料管理（头像、研究方向、简介）
- 成员列表展示

###  工作计划
- 每日计划添加/编辑/删除
- 计划完成状态标记
- 日历视图/列表视图切换

###  科研成果
- 论文、专利、奖项等成果记录
- 成果类型分类
- 个人成果管理

###  文档中心
- 文件上传/下载
- 在线预览（支持 PDF、图片、TXT）
- 文档公开/私密设置

###  公告系统
- 发布实验室公告
- 置顶公告
- 发布时间显示

###  搜索功能
- 站内全局搜索
- 搜索成员、成果、文档、公告、计划

###  数据导出
- 导出成果为 CSV
- 导出计划为 CSV
- 导出成员为 CSV

###  消息系统
- 成员间留言
- 未读消息提醒

###  AI 助手
- 基于腾讯云混元大模型的智能问答
- 可查询实验室相关信息

## 技术栈

- **后端**: Django 5.2
- **数据库**: SQLite（默认）
- **前端**: HTML5 + CSS3 + JavaScript
- **AI**: 腾讯云混元大模型 API

## 项目结构

```
lab_hub/
├── lab_hub_project/          # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── lab_management/           # 主应用
│   ├── models.py           # 数据模型
│   ├── views.py            # 视图函数
│   ├── urls.py             # URL 路由
│   └── templates/          # 模板文件
├── templates/               # 基础模板
│   └── base.html
├── media/                  # 用户上传文件
│   ├── avatars/
│   └── documents/
└── manage.py
```

## 快速开始

### 1. 克隆项目
```bash
git clone <项目地址>
cd lab_hub
```

### 2. 创建虚拟环境
```bash
conda create -n Lab_hub python=3.11
conda activate Lab_hub
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
复制 `.env.example` 为 `.env` 并配置：
```env
SECRET_KEY=your-secret-key
DEBUG=True
AI_SECRET_ID=your-secret-id
AI_SECRET_KEY=your-secret-key
```

### 5. 初始化数据库
```bash
python manage.py migrate
python manage.py createsuperuser  # 创建管理员账号
```

### 6. 运行服务器
```bash
python manage.py runserver 0.0.0.0:8000
```

访问 http://localhost:8000

## 功能页面

| 页面 | URL | 说明 |
|------|-----|------|
| 首页 | `/` | 展示公告、成员、最近计划 |
| 成员列表 | `/members/` | 实验室所有成员 |
| 团队总览 | `/overview/` | 统计数据和导出功能 |
| 工作计划 | `/plans/` | 日历/列表视图 |
| 文档中心 | `/documents/` | 文档上传下载 |
| 公告列表 | `/announcements/` | 公告管理 |
| 我的主页 | `/my/` | 个人中心 |
| 用户资料 | `/user/<username>/` | 查看他人资料 |
| 搜索 | `/search/?q=关键词` | 全局搜索 |
| AI 助手 | 点击 😺 按钮 | 智能问答 |

## 权限说明

- **公开内容**: 成员列表、公开文档、公告
- **登录后可见**: 个人主页、消息、我的成果/计划/文档
- **管理员**: 可删除任何内容、管理用户

## 部署到生产环境

### 使用 Gunicorn
```bash
pip install gunicorn
gunicorn lab_hub_project.wsgi:application --bind 0.0.0.0:8000
```

### 使用 Docker
```bash
docker build -t lab-hub .
docker run -p 8000:8000 lab-hub
```

## 许可证

MIT License
