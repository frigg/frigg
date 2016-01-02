from django.db import migrations


def create_owners_from_projects(apps, schema_editor):
    Project = apps.get_model("builds", "Project")
    Owner = apps.get_model("owners", "Owner")
    for project in Project.objects.all():
        Owner.objects.create(
            name=project.name,
            members=project.members,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('owners', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_owners_from_projects),
    ]
