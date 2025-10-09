# Generated manually

from django.db import migrations, models
import uuid


def generate_uuids(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for user in User.objects.all():
        user.uuid_field = uuid.uuid4()
        user.save(update_fields=['uuid_field'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Add a temporary UUID field
        migrations.AddField(
            model_name='user',
            name='uuid_field',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        # Generate UUIDs for existing users
        migrations.RunPython(generate_uuids, migrations.RunPython.noop),
    ]