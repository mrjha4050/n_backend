# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_users_pdfurl_alter_users_profileurl_alter_users_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='pdfPublicId',
            field=models.CharField(blank=True, default='', help_text='Cloudinary public_id for PDF file', max_length=255, null=True),
        ),
    ]

