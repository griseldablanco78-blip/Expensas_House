"""Three-way snapshot merge: preserve web changes and detect concurrent edits."""
from copy import deepcopy


class SyncConflict(ValueError):
    pass


def merge_snapshot(current, incoming, baseline=None):
    result = deepcopy(current)
    for key in ('stock', 'shopping', 'expenses', 'offers'):
        if incoming.get(key) is None:
            continue
        remote = {r['id']: r for r in current.get(key, [])}
        local = {r['id']: r for r in incoming[key]}
        if baseline is None:
            # First pairing keeps the server version of shared IDs; imports new IDs.
            result[key] = list({**local, **remote}.values())
            continue
        base = {r['id']: r for r in baseline.get(key, [])}
        merged = {}
        for identity in base.keys() | remote.keys() | local.keys():
            old, left, right = base.get(identity), remote.get(identity), local.get(identity)
            if right == old:
                chosen = left
            elif left == old or left == right:
                chosen = right
            else:
                # Android models omit web-only metadata. Merge fields, not whole rows.
                if left is None or right is None or old is None:
                    raise SyncConflict(f'Conflicto en {key}: {identity}. Hay cambios en ambos dispositivos.')
                chosen = dict(left)
                for field, value in right.items():
                    if value == old.get(field):
                        continue
                    if left.get(field) != old.get(field) and left.get(field) != value:
                        raise SyncConflict(f'Conflicto en {key}: {identity}, campo {field}.')
                    chosen[field] = value
            if chosen is not None:
                merged[identity] = chosen
        result[key] = list(merged.values())
    prefs = incoming.get('user_prefs')
    if prefs is not None:
        # totalSpent is derived from expense changes, never overwritten by stale clients.
        old_budget = (baseline or {}).get('user_prefs', {}).get('monthlyBudget')
        budget = prefs.get('monthlyBudget', 0)
        remote_budget = current['user_prefs'].get('monthlyBudget', 0)
        if baseline is None:
            if not remote_budget:
                result['user_prefs']['monthlyBudget'] = budget
        elif budget != old_budget:
            if remote_budget != old_budget and remote_budget != budget:
                raise SyncConflict('El presupuesto cambió en ambos dispositivos.')
            result['user_prefs']['monthlyBudget'] = budget
    delta = sum(e.get('amount', 0) for e in result['expenses']) - sum(e.get('amount', 0) for e in current['expenses'])
    result['user_prefs']['totalSpent'] = round(current['user_prefs'].get('totalSpent', 0) + delta, 2)
    return result
