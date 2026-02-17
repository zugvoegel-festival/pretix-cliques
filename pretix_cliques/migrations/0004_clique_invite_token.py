# Generated manually for non-enumerable invite links

from django.db import migrations, models


def _generate_invite_token():
    from django.utils.crypto import get_random_string
    return get_random_string(16, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')


def backfill_invite_tokens(apps, schema_editor):
    Clique = apps.get_model('pretix_cliques', 'Clique')
    used = set()
    for clique in Clique.objects.filter(invite_token__isnull=True):
        while True:
            token = _generate_invite_token()
            if token not in used and not Clique.objects.filter(invite_token=token).exists():
                used.add(token)
                clique.invite_token = token
                clique.save(update_fields=['invite_token'])
                break


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pretix_cliques', '0003_orderraffleoverride'),
    ]

    operations = [
        migrations.AddField(
            model_name='clique',
            name='invite_token',
            field=models.CharField(blank=True, db_index=True, max_length=24, null=True),
        ),
        migrations.RunPython(backfill_invite_tokens, reverse_noop),
        migrations.AlterField(
            model_name='clique',
            name='invite_token',
            field=models.CharField(
                db_index=True,
                help_text='Short token for the public invite link; not enumerable.',
                max_length=24,
                unique=True,
                null=False,
            ),
        ),
    ]
