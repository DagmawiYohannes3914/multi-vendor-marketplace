# Generated manually

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_prepare_uuid_migration'),
        ('profiles', '0001_initial'),
        ('admin', '0003_logentry_add_action_flag_choices'),
        ('authtoken', '0003_tokenproxy'),
    ]

    operations = [
        # For SQLite development, this is a no-op migration
        # The actual PostgreSQL migration would update foreign keys to use UUID
        migrations.RunSQL(
            # PostgreSQL version
            sql="SELECT 1;",
            # SQLite version - no-op for local development
            reverse_sql="SELECT 1;"
        ),
    ]