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


# H=Hit  S=Stand  D=Double  P=Split  R=Surrender
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


def get_advice(hand: list, dealer_card: str | None) -> dict:
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

    # Pair check (only meaningful with exactly 2 cards)
    if _is_pair(hand):
        pk = _pair_key(hand)
        action = PAIR_STRATEGY[pk][dealer]
        if action == 'D' and not can_double:
            action = 'H'
        return {
            'action': action,
            'action_name': ACTION_NAMES[action],
            'reason': _build_reason(action, f'par de {pk}s', dealer, can_double, can_surrender),
            'color': ACTION_COLORS[action],
        }

    # Soft hand
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
    action = HARD_STRATEGY[lookup][dealer]

    # Handle double not available
    if action == 'D' and not can_double:
        action = 'H'

    # Handle surrender not available → apply fallback
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
