"""
Blackjack logic: Hi-Lo counting, perfect basic strategy, and recommendations.
"""

HILO_VALUES = {
    '2': 1, '3': 1, '4': 1, '5': 1, '6': 1,
    '7': 0, '8': 0, '9': 0,
    '10': -1, 'J': -1, 'Q': -1, 'K': -1, 'A': -1,
}

VALID_CARDS = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}


def card_numeric_value(card: str) -> int:
    if card in ('J', 'Q', 'K', '10'):
        return 10
    if card == 'A':
        return 11
    return int(card)


def dealer_upcard_key(card: str):
    """Normalize dealer card for strategy table lookup."""
    if card in ('J', 'Q', 'K'):
        return 10
    if card == 'A':
        return 'A'
    return int(card)


def hand_total(cards: list) -> tuple:
    """Returns (total, is_soft). Soft = at least one ace counting as 11."""
    total = sum(card_numeric_value(c) for c in cards)
    aces = cards.count('A')
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total, aces > 0


def _is_pair(cards: list) -> bool:
    if len(cards) != 2:
        return False
    def norm(c):
        return '10' if c in ('10', 'J', 'Q', 'K') else c
    return norm(cards[0]) == norm(cards[1])


def _pair_key(cards: list) -> str:
    c = cards[0]
    return '10' if c in ('J', 'Q', 'K') else c


HARD_STRATEGY = {
    5:  {2:'H',3:'H',4:'H',5:'H',6:'H',7:'H',8:'H',9:'H',10:'H','A':'H'},
    6:  {2:'H',3:'H',4:'H',5:'H',6:'H',7:'H',8:'H',9:'H',10:'H','A':'H'},
    7:  {2:'H',3:'H',4:'H',5:'H',6:'H',7:'H',8:'H',9:'H',10:'H','A':'H'},
    8:  {2:'H',3:'H',4:'H',5:'H',6:'H',7:'H',8:'H',9:'H',10:'H','A':'H'},
    9:  {2:'H',3:'D',4:'D',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    10: {2:'D',3:'D',4:'D',5:'D',6:'D',7:'D',8:'D',9:'D',10:'H','A':'H'},
    11: {2:'D',3:'D',4:'D',5:'D',6:'D',7:'D',8:'D',9:'D',10:'D','A':'H'},
    12: {2:'H',3:'H',4:'S',5:'S',6:'S',7:'H',8:'H',9:'H',10:'H','A':'H'},
    13: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'H',8:'H',9:'H',10:'H','A':'H'},
    14: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'H',8:'H',9:'H',10:'H','A':'H'},
    15: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'H',8:'H',9:'H',10:'R','A':'R'},
    16: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'H',8:'H',9:'R',10:'R','A':'R'},
}

# Fallback when surrender is not available (>2 cards or casino doesn't offer it)
SURRENDER_FALLBACK = {
    15: {10: 'H', 'A': 'H'},
    16: {9: 'S', 10: 'S', 'A': 'H'},
}

SOFT_STRATEGY = {
    13: {2:'H',3:'H',4:'H',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    14: {2:'H',3:'H',4:'H',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    15: {2:'H',3:'H',4:'D',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    16: {2:'H',3:'H',4:'D',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    17: {2:'H',3:'D',4:'D',5:'D',6:'D',7:'H',8:'H',9:'H',10:'H','A':'H'},
    18: {2:'S',3:'D',4:'D',5:'D',6:'D',7:'S',8:'S',9:'H',10:'H','A':'H'},
    19: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
    20: {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
}

PAIR_STRATEGY = {
    'A':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'P',8:'P',9:'P',10:'P','A':'P'},
    '2':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'P',8:'H',9:'H',10:'H','A':'H'},
    '3':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'P',8:'H',9:'H',10:'H','A':'H'},
    '4':  {2:'H',3:'H',4:'H',5:'P',6:'P',7:'H',8:'H',9:'H',10:'H','A':'H'},
    '5':  {2:'D',3:'D',4:'D',5:'D',6:'D',7:'D',8:'D',9:'D',10:'H','A':'H'},
    '6':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'H',8:'H',9:'H',10:'H','A':'H'},
    '7':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'P',8:'H',9:'H',10:'H','A':'H'},
    '8':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'P',8:'P',9:'P',10:'P','A':'P'},
    '9':  {2:'P',3:'P',4:'P',5:'P',6:'P',7:'S',8:'P',9:'P',10:'S','A':'S'},
    '10': {2:'S',3:'S',4:'S',5:'S',6:'S',7:'S',8:'S',9:'S',10:'S','A':'S'},
}

INSURANCE_INDEX = 3  # Tomar seguro cuando TC >= +3

# Illustrious 18 — desviaciones Hi-Lo multi-mazo más valiosas
# Clave: (tipo, total_jugador, upcard_dealer)
# Valor: (índice_TC, acción_desviación, condición)
#   'gte': aplicar cuando TC >= índice  (cuentas positivas)
#   'lt' : aplicar cuando TC <  índice  (cuentas negativas)
ILLUSTRIOUS_18 = {
    ('hard', 16, 10): ( 0, 'S', 'gte'),  # básica R/H → Plantarse con TC >= 0
    ('hard', 16,  9): ( 5, 'S', 'gte'),  # básica R/H → Plantarse con TC >= 5
    ('hard', 15, 10): ( 4, 'S', 'gte'),  # básica R/H → Plantarse con TC >= 4
    ('hard', 13,  2): (-1, 'H', 'lt'),   # básica S   → Pedir   con TC < -1
    ('hard', 13,  3): (-2, 'H', 'lt'),   # básica S   → Pedir   con TC < -2
    ('hard', 12,  2): ( 3, 'S', 'gte'),  # básica H   → Plantarse con TC >= 3
    ('hard', 12,  3): ( 2, 'S', 'gte'),  # básica H   → Plantarse con TC >= 2
    ('hard', 12,  4): ( 0, 'H', 'lt'),   # básica S   → Pedir   con TC < 0
    ('hard', 12,  5): (-2, 'H', 'lt'),   # básica S   → Pedir   con TC < -2
    ('hard', 12,  6): (-1, 'H', 'lt'),   # básica S   → Pedir   con TC < -1
    ('hard', 10, 10): ( 4, 'D', 'gte'),  # básica H   → Doblar  con TC >= 4
    ('hard', 10, 'A'):( 4, 'D', 'gte'),  # básica H   → Doblar  con TC >= 4
    ('hard', 11, 'A'):( 1, 'D', 'gte'),  # básica H   → Doblar  con TC >= 1
    ('hard',  9,  2): ( 1, 'D', 'gte'),  # básica H   → Doblar  con TC >= 1
    ('hard',  9,  7): ( 3, 'D', 'gte'),  # básica H   → Doblar  con TC >= 3
    # Pares de 10s
    ('pair', '10',  5): ( 5, 'P', 'gte'),  # básica S → Separar con TC >= 5
    ('pair', '10',  6): ( 4, 'P', 'gte'),  # básica S → Separar con TC >= 4
}

ACTION_NAMES = {
    'H': 'HIT',
    'S': 'STAND',
    'D': 'DOUBLE DOWN',
    'P': 'SPLIT',
    'R': 'SURRENDER',
}

ACTION_COLORS = {
    'H': 'hit',
    'S': 'stand',
    'D': 'double',
    'P': 'split',
    'R': 'surrender',
    'blackjack': 'blackjack',
    'bust': 'bust',
}


def _i18_deviation(hand_type: str, total_or_pk, dealer, true_count: float, can_double: bool):
    """Returns deviation dict if an I18 index play applies, else None."""
    key = (hand_type, total_or_pk, dealer)
    entry = ILLUSTRIOUS_18.get(key)
    if entry is None:
        return None
    idx, dev_action, cond = entry
    applies = (true_count >= idx) if cond == 'gte' else (true_count < idx)
    if not applies:
        return None
    action = dev_action
    if action == 'D' and not can_double:
        action = 'H'
    return {
        'action': action,
        'action_name': ACTION_NAMES[action],
        'color': ACTION_COLORS[action],
        'is_deviation': True,
        'deviation_index': idx,
        'deviation_index_str': f'{idx:+d}',
    }


def get_advice(hand: list, dealer_card: str | None, true_count: float = 0.0) -> dict:
    if not hand:
        return {'action': None, 'action_name': '—', 'reason': 'Ingresa tus cartas para ver el consejo.', 'color': 'none'}
    if not dealer_card:
        return {'action': None, 'action_name': '—', 'reason': 'Ingresa la carta visible del dealer.', 'color': 'none'}

    total, is_soft = hand_total(hand)
    dealer = dealer_upcard_key(dealer_card)
    can_double = len(hand) == 2
    can_surrender = len(hand) == 2

    if total > 21:
        return {'action': 'bust', 'action_name': 'BUST', 'reason': f'Total {total}. Te pasaste.', 'color': 'bust'}

    if total == 21:
        if len(hand) == 2:
            return {'action': 'blackjack', 'action_name': '¡BLACKJACK!', 'reason': '¡Blackjack natural! Cobras 3:2.', 'color': 'blackjack'}
        return {'action': 'S', 'action_name': 'STAND', 'reason': 'Total 21. Plantarse siempre.', 'color': 'stand'}

    # Pair check — I18 overrides (split 10s) before basic pair strategy
    if _is_pair(hand):
        pk = _pair_key(hand)
        dev = _i18_deviation('pair', pk, dealer, true_count, can_double)
        if dev:
            basic = PAIR_STRATEGY[pk][dealer]
            dev['reason'] = (f'I18: par de {pk}s vs {_dealer_str(dealer)} — '
                             f'TC {true_count:+.1f} (índice {dev["deviation_index_str"]}). '
                             f'Básica: {ACTION_NAMES.get(basic, basic)}')
            return dev
        action = PAIR_STRATEGY[pk][dealer]
        if action == 'D' and not can_double:
            action = 'H'
        return {
            'action': action,
            'action_name': ACTION_NAMES[action],
            'reason': _build_reason(action, f'par de {pk}s', dealer, can_double, can_surrender),
            'color': ACTION_COLORS[action],
        }

    # Soft hand (no I18 deviations for soft totals)
    if is_soft and 13 <= total <= 20:
        action = SOFT_STRATEGY[total][dealer]
        if action == 'D' and not can_double:
            action = 'H'
        return {
            'action': action,
            'action_name': ACTION_NAMES[action],
            'reason': _build_reason(action, f'soft {total}', dealer, can_double, can_surrender),
            'color': ACTION_COLORS[action],
        }

    # Hard hand
    if total >= 17:
        return {'action': 'S', 'action_name': 'STAND', 'reason': f'Hard {total}. Plantarse con 17+.', 'color': 'stand'}

    lookup = max(5, min(total, 16))
    basic_action = HARD_STRATEGY[lookup][dealer]

    # Check I18 BEFORE resolving surrender — I18 can override even surrender
    dev = _i18_deviation('hard', lookup, dealer, true_count, can_double)
    if dev:
        # Describe what basic strategy would do
        if basic_action == 'R':
            if can_surrender:
                basic_label = 'SURRENDER'
            else:
                fb = SURRENDER_FALLBACK.get(lookup, {}).get(dealer, 'H')
                basic_label = ACTION_NAMES.get(fb, fb)
        elif basic_action == 'D' and not can_double:
            basic_label = 'HIT'
        else:
            basic_label = ACTION_NAMES.get(basic_action, basic_action)
        if dev['action'] != basic_action:
            dev['reason'] = (f'I18: hard {total} vs {_dealer_str(dealer)} — '
                             f'TC {true_count:+.1f} (índice {dev["deviation_index_str"]}). '
                             f'Básica: {basic_label}')
            return dev

    # Normal flow (no I18 override)
    action = basic_action
    if action == 'D' and not can_double:
        action = 'H'

    if action == 'R':
        if can_surrender:
            fb = SURRENDER_FALLBACK.get(lookup, {}).get(dealer, 'H')
            reason = _build_reason('R', f'hard {total}', dealer, can_double, can_surrender, fallback=fb)
            return {'action': 'R', 'action_name': 'SURRENDER', 'reason': reason, 'color': 'surrender'}
        else:
            action = SURRENDER_FALLBACK.get(lookup, {}).get(dealer, 'H')

    return {
        'action': action,
        'action_name': ACTION_NAMES[action],
        'reason': _build_reason(action, f'hard {total}', dealer, can_double, can_surrender),
        'color': ACTION_COLORS[action],
    }


def _dealer_str(dealer) -> str:
    return 'As' if dealer == 'A' else str(dealer)


def _build_reason(action: str, hand_desc: str, dealer, can_double: bool, can_surrender: bool, fallback: str = None) -> str:
    d = _dealer_str(dealer)
    base = f'{hand_desc} vs dealer {d}'
    if action == 'H':
        return f'{base}: Pedir carta.'
    if action == 'S':
        return f'{base}: Plantarse.'
    if action == 'D':
        return f'{base}: Doblar apuesta.'
    if action == 'P':
        return f'{base}: Separar el par.'
    if action == 'R':
        fb_name = ACTION_NAMES.get(fallback, 'Hit') if fallback else 'Hit'
        return f'{base}: Rendirse (probabilidad de ganar < 25%). Si no hay rendición → {fb_name}.'
    return base


def get_true_count(running_count: int, cards_seen: int, num_decks: int) -> float:
    total_cards = num_decks * 52
    remaining = max(total_cards - cards_seen, 26)  # minimum ~0.5 deck
    remaining_decks = remaining / 52
    return round(running_count / remaining_decks, 2)


def calculate_hand_result(hand_cards: list, hand_total_val: int, dealer_total: int, dealer_hand: list) -> str:
    """Returns 'blackjack', 'win', 'push', or 'loss' for one hand vs dealer."""
    if hand_total_val > 21:
        return 'loss'
    player_bj = len(hand_cards) == 2 and hand_total_val == 21
    dealer_bj  = len(dealer_hand) == 2 and dealer_total == 21
    if player_bj and not dealer_bj:
        return 'blackjack'
    if player_bj and dealer_bj:
        return 'push'
    if dealer_total > 21:
        return 'win'
    if hand_total_val > dealer_total:
        return 'win'
    if hand_total_val < dealer_total:
        return 'loss'
    return 'push'


def calculate_round_pnl(my_hands: list, dealer_hand: list, dealer_total: int, bet: float):
    """
    Returns (pnl, summary_result, per_hand_results).
    my_hands: list of card lists (one per hand).
    pnl is relative to a single bet unit; blackjack pays 1.5x.
    """
    hand_results = []
    total_pnl = 0.0
    for hand in my_hands:
        if not hand:
            continue
        tot, _ = hand_total(hand)
        res = calculate_hand_result(hand, tot, dealer_total, dealer_hand)
        hand_results.append(res)
        if res == 'blackjack':
            total_pnl += bet * 1.5
        elif res == 'win':
            total_pnl += bet
        elif res == 'loss':
            total_pnl -= bet
        # push: 0

    if not hand_results:
        return 0.0, 'push', []

    summary = 'win' if total_pnl > 0 else ('loss' if total_pnl < 0 else 'push')
    return round(total_pnl, 2), summary, hand_results


def get_recommended_bet(true_count: float, min_bet: float, max_bet: float) -> float:
    """Returns recommended bet based on Hi-Lo true count spread (1-2-4-8 units)."""
    if true_count < 1:
        mult = 1
    elif true_count < 2:
        mult = 2
    elif true_count < 3:
        mult = 4
    else:
        mult = 8
    return min(min_bet * mult, max_bet)


def get_entry_recommendation(true_count: float) -> dict:
    tc = true_count
    sign = '+' if tc >= 0 else ''
    if tc >= 3:
        return {
            'level': 'excellent',
            'text': '¡JUEGA! Apuesta fuerte',
            'detail': f'TC {sign}{tc:.1f} — Ventaja significativa del jugador.',
        }
    if tc >= 1:
        return {
            'level': 'good',
            'text': 'JUEGA — Favorable',
            'detail': f'TC {sign}{tc:.1f} — Ventaja del jugador. Buena ronda para entrar.',
        }
    if tc >= 0:
        return {
            'level': 'neutral',
            'text': 'NEUTRO',
            'detail': f'TC {sign}{tc:.1f} — Sin ventaja clara. Juego equilibrado.',
        }
    if tc >= -1:
        return {
            'level': 'caution',
            'text': 'PRECAUCIÓN',
            'detail': f'TC {sign}{tc:.1f} — Ligera ventaja de la casa.',
        }
    return {
        'level': 'bad',
        'text': 'NO JUEGUES',
        'detail': f'TC {sign}{tc:.1f} — Ventaja significativa de la casa. Espera mejor momento.',
    }
