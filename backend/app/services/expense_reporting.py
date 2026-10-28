"""Calendar-month reporting; legacy accumulated totals remain compatible with Android."""
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import re

from backend.app.infrastructure.json_store import get_expenses, get_user_prefs
from backend.app.services.receipt_scanning import cents

HOUSEHOLD_TZ = timezone(timedelta(hours=-3))


def expense_date(expense):
    if expense.get('purchase_date'):
        return expense['purchase_date']
    stamp = expense.get('timestamp')
    return datetime.fromtimestamp(stamp / 1000, HOUSEHOLD_TZ).date().isoformat() if stamp else ''


def monthly_summary(month):
    if not re.fullmatch(r'\d{4}-(?:0[1-9]|1[0-2])', month) or month.startswith('0000'):
        raise ValueError('Elegí un mes válido con formato AAAA-MM.')
    expenses = [e for e in get_expenses() if expense_date(e).startswith(month + '-')]
    stores = defaultdict(float)
    for expense in expenses:
        stores[expense.get('store') or expense.get('note') or 'Sin supermercado'] += expense['amount']
    spent = cents(sum(e['amount'] for e in expenses))
    budget = get_user_prefs().get('monthlyBudget', 0)
    return {'month': month, 'monthlyBudget': budget, 'totalSpent': spent,
            'remaining': cents(budget - spent), 'count': len(expenses),
            'by_store': [{'store': name, 'amount': cents(amount)} for name, amount in sorted(stores.items())]}
