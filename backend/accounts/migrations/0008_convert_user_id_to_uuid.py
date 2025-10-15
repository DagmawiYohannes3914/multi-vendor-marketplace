from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_user_uuid_field'),
        ('profiles', '0002_alter_customerprofile_id_alter_vendorprofile_id'),
        ('products', '0002_alter_category_id_alter_inventorytransaction_id_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
            DO $$
            DECLARE r RECORD;
            BEGIN
              -- Ensure temporary UUID column exists (legacy path support)
              IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'accounts_user' AND column_name = 'uuid_field'
              ) THEN
                EXECUTE 'ALTER TABLE accounts_user ADD COLUMN uuid_field uuid NULL';
              END IF;

              -- Drop FK constraints referencing accounts_user (safety for PK type change)
              FOR r IN (
                SELECT conname, conrelid::regclass AS table_name
                FROM pg_constraint
                WHERE contype = 'f'
                  AND confrelid::regclass::text = 'accounts_user'
              ) LOOP
                EXECUTE format('ALTER TABLE %s DROP CONSTRAINT IF EXISTS %I', r.table_name, r.conname);
              END LOOP;

              -- Convert id to uuid if it is not already uuid
              IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'accounts_user' AND column_name = 'id' AND data_type <> 'uuid'
              ) THEN
                -- Drop identity if present
                IF EXISTS (
                  SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'accounts_user' AND column_name = 'id' AND is_identity = 'YES'
                ) THEN
                  EXECUTE 'ALTER TABLE accounts_user ALTER COLUMN id DROP IDENTITY';
                END IF;
                -- Drop default if present (safe regardless)
                EXECUTE 'ALTER TABLE accounts_user ALTER COLUMN id DROP DEFAULT';
                -- Convert to uuid using existing uuid_field mapping
                EXECUTE 'ALTER TABLE accounts_user ALTER COLUMN id TYPE uuid USING uuid_field';
              END IF;

              -- Drop temporary uuid_field if it exists
              IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='accounts_user' AND column_name='uuid_field'
              ) THEN
                EXECUTE 'ALTER TABLE accounts_user DROP COLUMN uuid_field';
              END IF;
            END $$;
            ''',
            reverse_sql='SELECT 1;'
        )
    ]