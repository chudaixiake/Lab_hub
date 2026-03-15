from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('lab_management', '0008_userprofile_email_userprofile_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='发布时间'),
            preserve_default=False,
        ),
    ]
