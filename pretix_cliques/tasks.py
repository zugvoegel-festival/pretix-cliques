from collections import defaultdict

from django.db.models import OuterRef, Count, Subquery, IntegerField
from pretix_cliques.models import OrderRaffleOverride

from pretix.base.models import SubEvent, Order, Event, OrderPosition, User
from pretix.base.services.orders import approve_order, OrderError, deny_order
from pretix.base.services.tasks import EventTask
from pretix.celery_app import app
import random


@app.task(bind=True, base=EventTask)
def run_raffle(self, event: Event, subevent_id: int, user_id: int, raffle_size: int, max_addons: int):
    subevent = SubEvent.objects.get(pk=subevent_id) if subevent_id else None
    user = User.objects.get(pk=user_id)

    other_subevent_count = OrderPosition.objects.filter(
        order=OuterRef('pk'),
        item__admission=True
    ).exclude(
        subevent_id=subevent_id,
    ).order_by().values('order').annotate(k=Count('id')).values('k')

    subevent_count = OrderPosition.objects.filter(
        order=OuterRef('pk'),
        subevent_id=subevent_id,
        addon_to__isnull=True,
        item__admission=True
    ).order_by().values('order').annotate(k=Count('id')).values('k')

    addon_subevent_count = OrderPosition.objects.filter(
        order=OuterRef('pk'),
        subevent_id=subevent_id,
        addon_to__isnull=False,
        item__admission=True
    ).order_by().values('order').annotate(k=Count('id')).values('k')

    eligible_orders = event.orders.annotate(
        pcnt_othersub=Subquery(other_subevent_count, output_field=IntegerField()),
        pcnt_subevent=Subquery(subevent_count, output_field=IntegerField()),
        acnt_subevent=Subquery(addon_subevent_count, output_field=IntegerField()),
    ).filter(
        pcnt_othersub__isnull=True,
        pcnt_subevent__gte=1,
        require_approval=True,
        status=Order.STATUS_PENDING,
    ).select_related('raffle_override', 'orderclique', 'orderclique__clique').prefetch_related('positions')

    clique_ids_remove = set()
    raffle_keys_prefer = set()
    raffle_tickets = defaultdict(list)

    for order in eligible_orders:
        try:
            rom = order.raffle_override.mode
        except OrderRaffleOverride.DoesNotExist:
            rom = None

        if rom == OrderRaffleOverride.MODE_NEVER:
            # banned ticket, ban whole clique
            if getattr(order, 'orderclique', None):
                clique_ids_remove.add(order.orderclique.clique_id)
            continue

        if getattr(order, 'orderclique', None):
            raffle_tickets['clique', order.orderclique.clique_id].append(order)
            if rom == OrderRaffleOverride.MODE_ALWAYS:
                raffle_keys_prefer.add(('clique', order.orderclique.clique_id))
        else:
            raffle_tickets['order', order.code].append(order)
            if rom == OrderRaffleOverride.MODE_ALWAYS:
                raffle_keys_prefer.add(('order', order.code))

    for k in clique_ids_remove:
        try:
            del raffle_tickets['clique', k]
            raffle_keys_prefer.remove(('clique', k))
        except KeyError:
            pass

    raffle_keys_not_preferred = [k for k in raffle_tickets.keys() if k not in raffle_keys_prefer]
    random.shuffle(raffle_keys_not_preferred)

    raffle_order = list(raffle_keys_prefer) + raffle_keys_not_preferred
    approvals_left = raffle_size
    addons_left = max_addons

    orders_to_approve = []

    while raffle_order and approvals_left > 0:
        orders = raffle_tickets[raffle_order.pop(0)]

        n_tickets = 0
        for o in orders:
            if o.pcnt_subevent is not None:
                n_tickets += o.pcnt_subevent

        n_addons = 0
        for o in orders:
            if o.acnt_subevent is not None:
                n_addons += o.acnt_subevent

        if n_addons > addons_left:
            # We do not have enough add-ons left to service this raffle ticket, skip to the
            # next one, sorry.
            continue

        # We do not skip if n_tickets < approvals_left, so we prefer giving out a few more
        # tickets than planned over a few less. This is intentional / accepted behaviour.

        orders_to_approve += orders
        approvals_left -= n_tickets
        addons_left -= n_addons

    self.update_state(
        state='PROGRESS',
        meta={'value': 0}
    )
    for i, order in enumerate(orders_to_approve):
        try:
            approve_order(
                order,
                user=user,
                send_mail=True,
            )
        except OrderError as e:
            order.log_action('pretix_cliques.raffle.approve_failed', data={'detail': str(e)}, user=user)
        if i % 50 == 0:
            self.update_state(
                state='PROGRESS',
                meta={'value': round(i / len(orders_to_approve) * 100, 2)}
            )

    return len(orders_to_approve)


@app.task(bind=True, base=EventTask)
def run_rejection(self, event: Event, subevent_id: int, user_id: int):
    user = User.objects.get(pk=user_id)

    subevent_count = OrderPosition.objects.filter(
        order=OuterRef('pk'),
        subevent_id=subevent_id,
        item__admission=True
    ).order_by().values('order').annotate(k=Count('id')).values('k')
    orders = list(event.orders.annotate(
        pcnt_subevent=Subquery(subevent_count, output_field=IntegerField()),
    ).filter(
        pcnt_subevent__gte=1,
        require_approval=True,
        status=Order.STATUS_PENDING,
    ))
    self.update_state(
        state='PROGRESS',
        meta={'value': 0}
    )
    for i, order in enumerate(orders):
        deny_order(
            order,
            user=user,
            send_mail=True,
        )
        if i % 50 == 0:
            self.update_state(
                state='PROGRESS',
                meta={'value': round(i / len(orders) * 100, 2)}
            )

    return len(orders)
