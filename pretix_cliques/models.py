from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from pretix.base.models import LoggedModel


def _generate_invite_token():
    return get_random_string(16, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')


class Clique(LoggedModel):
    event = models.ForeignKey('pretixbase.Event', on_delete=models.CASCADE, related_name='cliques')
    name = models.CharField(max_length=190)
    password = models.CharField(max_length=190, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    invite_token = models.CharField(
        max_length=24,
        unique=True,
        db_index=True,
        blank=True,
        help_text=_('Short token for the public invite link; not enumerable.'),
    )

    class Meta:
        unique_together = (('event', 'name'),)
        ordering = ('name',)

    def save(self, *args, **kwargs):
        if not self.invite_token:
            while True:
                token = _generate_invite_token()
                if not Clique.objects.filter(invite_token=token).exists():
                    self.invite_token = token
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class OrderClique(models.Model):
    order = models.OneToOneField('pretixbase.Order', related_name='orderclique', on_delete=models.CASCADE)
    clique = models.ForeignKey(Clique, related_name='ordercliques', on_delete=models.CASCADE,
                               verbose_name=_('Clique'))
    is_admin = models.BooleanField(default=False, verbose_name=_('Clique administrator'))


class OrderRaffleOverride(models.Model):
    MODE_ALWAYS = 'always'
    MODE_NEVER = 'never'
    MODE_NORMAL = 'chance'
    MODE_CHOICES = (
        (MODE_ALWAYS, _('always chosen')),
        (MODE_NEVER, _('never chosen')),
        (MODE_NORMAL, _('normal chance'))
    )

    order = models.OneToOneField('pretixbase.Order', related_name='raffle_override', on_delete=models.CASCADE)
    mode = models.CharField(max_length=180, choices=MODE_CHOICES)
