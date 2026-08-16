from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ordering", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="userorder",
            name="one_order_per_user_cycle",
        ),
    ]
