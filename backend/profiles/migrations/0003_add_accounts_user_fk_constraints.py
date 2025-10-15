from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_convert_user_id_to_uuid'),
        ('profiles', '0002_alter_customerprofile_id_alter_vendorprofile_id'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE profiles_customerprofile ADD CONSTRAINT profiles_customerprofile_user_id_fk FOREIGN KEY (user_id) REFERENCES accounts_user(id);",
                "ALTER TABLE profiles_vendorprofile ADD CONSTRAINT profiles_vendorprofile_user_id_fk FOREIGN KEY (user_id) REFERENCES accounts_user(id);",
            ],
            reverse_sql=[
                "ALTER TABLE profiles_customerprofile DROP CONSTRAINT IF EXISTS profiles_customerprofile_user_id_fk;",
                "ALTER TABLE profiles_vendorprofile DROP CONSTRAINT IF EXISTS profiles_vendorprofile_user_id_fk;",
            ]
        )
    ]