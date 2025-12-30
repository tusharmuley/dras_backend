# Generated manually to migrate category data from text to ForeignKey

import uuid
from django.db import migrations
from django.conf import settings


def migrate_category_data_forward(apps, schema_editor):
    """
    Migrate existing text category values to Category ForeignKey references.
    This creates Category records and uses raw SQL to add temporary columns for the IDs.
    """
    Category = apps.get_model('documents', 'Category')
    UploadedDocument = apps.get_model('documents', 'UploadedDocument')
    DocumentAudit = apps.get_model('documents', 'DocumentAudit')
    User = apps.get_model(settings.AUTH_USER_MODEL)
    
    # Get or create a default user for categories
    try:
        default_user = User.objects.filter(role__in=['super_admin', 'admin']).first()
        if not default_user:
            default_user = User.objects.first()
    except Exception:
        default_user = None
    
    if not default_user:
        print("Warning: No users found. Skipping category data migration.")
        return
    
    # Dictionary to map category text to Category IDs
    category_id_map = {}
    
    # Get all unique category values from UploadedDocument
    try:
        uploaded_docs = UploadedDocument.objects.exclude(category__isnull=True).exclude(category='')
        unique_categories = list(uploaded_docs.values_list('category', flat=True).distinct())
    except Exception:
        unique_categories = []
    
    # Get all unique category values from DocumentAudit
    try:
        audit_old_categories = list(DocumentAudit.objects.exclude(old_category__isnull=True).exclude(old_category='').values_list('old_category', flat=True).distinct())
        audit_new_categories = list(DocumentAudit.objects.exclude(new_category__isnull=True).exclude(new_category='').values_list('new_category', flat=True).distinct())
    except Exception:
        audit_old_categories = []
        audit_new_categories = []
    
    # Combine all unique categories
    all_unique_categories = set(unique_categories) | set(audit_old_categories) | set(audit_new_categories)
    
    # Create Category records for each unique category text
    for category_text in all_unique_categories:
        if category_text and category_text.strip():
            try:
                category_obj = Category.objects.get(category=category_text)
            except Category.DoesNotExist:
                category_obj = Category.objects.create(
                    id=uuid.uuid4(),
                    category=category_text,
                    created_by=default_user,
                    is_active=True
                )
            category_id_map[category_text] = str(category_obj.id)
    
    print(f"Created {len(category_id_map)} category records")


def migrate_category_data_backward(apps, schema_editor):
    """
    Reverse migration: Delete created Category records (optional - usually not needed).
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0006_category'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(migrate_category_data_forward, migrate_category_data_backward),
    ]
