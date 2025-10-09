# Generated manually

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_update_foreign_keys'),
    ]

    operations = [
        # For SQLite development, this is a no-op migration
        # The actual PostgreSQL migration would update the User primary key to UUID
        migrations.RunSQL(
            sql="SELECT 1;",
            reverse_sql="SELECT 1;"
        ),
    ]