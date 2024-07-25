# Default Locations
from django.dispatch import receiver
from django.db.models.signals import post_migrate


@receiver(post_migrate)
def create_default_building(sender, **kwargs):
    if sender.label == "users":
        apps = kwargs.get("apps")
        try:
            BuildingModel = apps.get_model("equipment", "Building")
        except Exception as e:
            print(f"Error retrieving Building model: {str(e)}")
            return

        # List of buildings to create
        buildings = [
            {"name": "Rowan Hall"},
            {"name": "Engineering Hall"},
        ]

        for building_data in buildings:
            name = building_data["name"]
            building, created = BuildingModel.objects.get_or_create(name=name)

            if created:
                # Building was newly created
                print(f'Building "{name}" created.')
            else:
                # Building already exists
                print(f'Building "{name}" already exists.')
