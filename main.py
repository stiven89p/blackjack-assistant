from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import blackjack as bj

app = FastAPI(title="Blackjack Assistant")

state = {
    'num_decks': None,
    'running_count': 0,
    'cards_seen': 0,
    'my_hands': [[]],   # list of hands; splits add new entries here
    'active_hand': 0,   # index of the hand currently being played
    'dealer_hand': [],
    'history': [],      # for undo support
    'session': {
        'active': False,
        'bankroll': 0.0,
        'initial_bankroll': 0.0,
        'min_bet': 0.0,
        'max_bet': 0.0,
        'round_history': [],        # list of archived rounds
        'current_round_cards': [],  # cards dealt in this round
        'round_num': 1,
        'recommended_bet_current': 0.0,  # bet captured at round start
    },
}


class SetupRequest(BaseModel):
    num_decks: int


class CardRequest(BaseModel):
    card: str
    target: str  # 'mine' | 'dealer' | 'other'


class SessionSetupRequest(BaseModel):
    bankroll: float
    min_bet: float
    max_bet: float


class RoundResultRequest(BaseModel):
    result: str  # 'win' | 'push' | 'loss'


@app.get("/", response_class=HTMLResponse)
def index():
    with open("index.html", encoding="utf-8") as f:
        return f.read()


@app.post("/api/setup")
def setup(req: SetupRequest):
    if req.num_decks not in (1, 2, 4, 6, 8):
        raise HTTPException(400, "Número de mazos debe ser 1, 2, 4, 6 u 8")
    state.update({
        'num_decks': req.num_decks,
        'running_count': 0,
        'cards_seen': 0,
        'my_hands': [[]],
        'active_hand': 0,
        'dealer_hand': [],
        'history': [],
    })
    return _build_response()


@app.post("/api/card")
def register_card(req: CardRequest):
    if state['num_decks'] is None:
        raise HTTPException(400, "Primero configura el número de mazos")
    if req.card not in bj.VALID_CARDS:
        raise HTTPException(400, f"Carta inválida: {req.card}")
    if req.target not in ('mine', 'dealer', 'other'):
        raise HTTPException(400, "Target debe ser 'mine', 'dealer' u 'other'")

    s = state['session']
    if s['active'] and len(s['current_round_cards']) == 0:
        # Capture recommended bet before first card changes the count
        tc_now = bj.get_true_count(state['running_count'], state['cards_seen'], state['num_decks'])
        s['recommended_bet_current'] = bj.get_recommended_bet(tc_now, s['min_bet'], s['max_bet'])

    state['running_count'] += bj.HILO_VALUES[req.card]
    state['cards_seen'] += 1
    state['history'].append({
        'action': 'card',
        'card': req.card,
        'target': req.target,
        'hand_index': state['active_hand'],
    })

    if s['active']:
        s['current_round_cards'].append(req.card)

    if req.target == 'mine':
        state['my_hands'][state['active_hand']].append(req.card)
    elif req.target == 'dealer':
        state['dealer_hand'].append(req.card)

    return _build_response()


@app.post("/api/split")
def split():
    hi = state['active_hand']
    hand = state['my_hands'][hi]
    if len(hand) != 2:
        raise HTTPException(400, "Se necesitan exactamente 2 cartas para separar")
    if not bj._is_pair(hand):
        raise HTTPException(400, "Las dos cartas deben tener el mismo valor")

    c1, c2 = hand[0], hand[1]
    # Current hand keeps c1; new hand [c2] is inserted immediately after
    state['my_hands'][hi] = [c1]
    state['my_hands'].insert(hi + 1, [c2])
    state['history'].append({'action': 'split', 'hand_index': hi, 'card2': c2})
    return _build_response()


@app.post("/api/next-hand")
def next_hand():
    if state['active_hand'] >= len(state['my_hands']) - 1:
        raise HTTPException(400, "No hay más manos pendientes")
    state['active_hand'] += 1
    state['history'].append({'action': 'next_hand'})
    return _build_response()


@app.post("/api/undo")
def undo():
    if not state['history']:
        return _build_response()

    last = state['history'].pop()

    if last['action'] == 'card':
        state['running_count'] -= bj.HILO_VALUES[last['card']]
        state['cards_seen'] = max(0, state['cards_seen'] - 1)
        hi = last['hand_index']
        if last['target'] == 'mine' and hi < len(state['my_hands']) and state['my_hands'][hi]:
            state['my_hands'][hi].pop()
        elif last['target'] == 'dealer' and state['dealer_hand']:
            state['dealer_hand'].pop()
        s = state['session']
        if s['active'] and s['current_round_cards']:
            s['current_round_cards'].pop()

    elif last['action'] == 'split':
        hi = last['hand_index']
        c2 = last['card2']
        if hi + 1 < len(state['my_hands']):
            state['my_hands'].pop(hi + 1)
        state['my_hands'][hi].append(c2)
        state['active_hand'] = hi

    elif last['action'] == 'next_hand':
        state['active_hand'] = max(0, state['active_hand'] - 1)

    return _build_response()


@app.post("/api/new-round")
def new_round():
    """Clears all hands and dealer hand, keeps deck count."""
    s = state['session']
    if s['active'] and s['current_round_cards']:
        nd = state['num_decks']
        tc = bj.get_true_count(state['running_count'], state['cards_seen'], nd)

        archived = {
            'round': s['round_num'],
            'cards': list(s['current_round_cards']),
            'tc_end': tc,
            'rc_end': state['running_count'],
            'recommended_bet': s['recommended_bet_current'],
            'result': None,
            'pnl': None,
            'hand_results': None,
        }

        # Auto-calculate result when possible
        dealer_hand = state['dealer_hand']
        my_hands    = [h for h in state['my_hands'] if h]
        if my_hands:
            all_bust = all(bj.hand_total(h)[0] > 21 for h in my_hands)
            dealer_total, _ = bj.hand_total(dealer_hand) if dealer_hand else (0, False)
            can_auto = all_bust or (bool(dealer_hand) and dealer_total >= 17)
            if can_auto:
                pnl, summary, hand_results = bj.calculate_round_pnl(
                    my_hands, dealer_hand, dealer_total, s['recommended_bet_current']
                )
                s['bankroll'] = round(s['bankroll'] + pnl, 2)
                archived['result']       = summary
                archived['pnl']         = pnl
                archived['hand_results'] = hand_results

        s['round_history'].append(archived)
        if len(s['round_history']) > 100:
            s['round_history'] = s['round_history'][-100:]
        s['round_num'] += 1
        s['current_round_cards'] = []

    state['my_hands'] = [[]]
    state['active_hand'] = 0
    state['dealer_hand'] = []
    state['history'] = []
    return _build_response()


@app.post("/api/new-shoe")
def new_shoe():
    """Full reset with same number of decks."""
    state.update({
        'running_count': 0,
        'cards_seen': 0,
        'my_hands': [[]],
        'active_hand': 0,
        'dealer_hand': [],
        'history': [],
    })
    return _build_response()


@app.get("/api/state")
def get_state():
    return _build_response()


@app.post("/api/session-setup")
def session_setup(req: SessionSetupRequest):
    if req.bankroll <= 0 or req.min_bet <= 0 or req.max_bet <= 0:
        raise HTTPException(400, "Los valores deben ser positivos")
    if req.min_bet > req.max_bet:
        raise HTTPException(400, "La apuesta mínima no puede ser mayor que la máxima")
    s = state['session']
    s.update({
        'active': True,
        'bankroll': round(req.bankroll, 2),
        'initial_bankroll': round(req.bankroll, 2),
        'min_bet': round(req.min_bet, 2),
        'max_bet': round(req.max_bet, 2),
        'round_history': [],
        'current_round_cards': [],
        'round_num': 1,
        'recommended_bet_current': round(req.min_bet, 2),
    })
    return _build_response()


@app.post("/api/round-result")
def round_result(req: RoundResultRequest):
    if req.result not in ('win', 'push', 'loss'):
        raise HTTPException(400, "Resultado debe ser 'win', 'push' o 'loss'")
    s = state['session']
    if not s['active'] or not s['round_history']:
        raise HTTPException(400, "No hay ronda archivada para registrar resultado")
    last = s['round_history'][-1]
    if last.get('result') is not None:
        raise HTTPException(400, "El resultado de esta ronda ya fue registrado")
    bet = last['recommended_bet']
    pnl = bet if req.result == 'win' else (-bet if req.result == 'loss' else 0.0)
    s['bankroll'] = round(s['bankroll'] + pnl, 2)
    last['result'] = req.result
    last['pnl'] = round(pnl, 2)
    return _build_response()


@app.post("/api/session-reset")
def session_reset():
    """Resets session stats without touching the shoe count."""
    s = state['session']
    if s['active']:
        s.update({
            'bankroll': s['initial_bankroll'],
            'round_history': [],
            'current_round_cards': [],
            'round_num': 1,
            'recommended_bet_current': s['min_bet'],
        })
    return _build_response()


def _build_response() -> dict:
    nd = state['num_decks']
    if nd is None:
        return {'setup_required': True}

    rc = state['running_count']
    cs = state['cards_seen']
    tc = bj.get_true_count(rc, cs, nd)
    remaining_decks = round(max((nd * 52 - cs), 26) / 52, 1)

    dealer_hand = state['dealer_hand']
    dealer_upcard = dealer_hand[0] if dealer_hand else None
    dealer_total, dealer_soft = bj.hand_total(dealer_hand) if dealer_hand else (None, False)

    active = state['active_hand']
    hands_info = []
    for i, hand in enumerate(state['my_hands']):
        total, is_soft = bj.hand_total(hand) if hand else (None, False)
        hands_info.append({'cards': hand, 'total': total, 'soft': is_soft})

    active_hand = state['my_hands'][active] if active < len(state['my_hands']) else []
    can_split = len(active_hand) == 2 and bj._is_pair(active_hand)
    has_next_hand = active < len(state['my_hands']) - 1

    advice = bj.get_advice(active_hand, dealer_upcard, tc)
    entry  = bj.get_entry_recommendation(tc)

    # Insurance recommendation when dealer shows Ace
    insurance = None
    if dealer_upcard == 'A' and active_hand:
        take = tc >= bj.INSURANCE_INDEX
        insurance = {
            'take': take,
            'reason': (f'TC {tc:+.1f} ≥ +{bj.INSURANCE_INDEX} — Toma el seguro (EV positivo)'
                       if take else
                       f'TC {tc:+.1f} < +{bj.INSURANCE_INDEX} — No tomes el seguro'),
        }

    s = state['session']
    session_data = None
    if s['active']:
        rec_bet = bj.get_recommended_bet(tc, s['min_bet'], s['max_bet'])
        has_pending = bool(s['round_history'] and s['round_history'][-1]['result'] is None)
        wins   = sum(1 for r in s['round_history'] if r['result'] == 'win')
        losses = sum(1 for r in s['round_history'] if r['result'] == 'loss')
        last_auto = None
        if s['round_history']:
            last = s['round_history'][-1]
            if last['result'] is not None and last['pnl'] is not None:
                last_auto = {'result': last['result'], 'pnl': last['pnl'],
                             'hand_results': last.get('hand_results', [])}
        session_data = {
            'active': True,
            'bankroll': s['bankroll'],
            'initial_bankroll': s['initial_bankroll'],
            'pnl_total': round(s['bankroll'] - s['initial_bankroll'], 2),
            'min_bet': s['min_bet'],
            'max_bet': s['max_bet'],
            'recommended_bet': rec_bet,
            'recommended_bet_current': s['recommended_bet_current'],
            'round_num': s['round_num'],
            'current_round_cards': s['current_round_cards'],
            'round_history': s['round_history'],
            'has_pending_result': has_pending,
            'last_auto_result': last_auto,
            'wins': wins,
            'losses': losses,
        }

    return {
        'setup_required': False,
        'num_decks': nd,
        'running_count': rc,
        'true_count': tc,
        'remaining_decks': remaining_decks,
        'cards_seen': cs,
        'hands': hands_info,
        'active_hand': active,
        'can_split': can_split,
        'has_next_hand': has_next_hand,
        'dealer_hand': dealer_hand,
        'dealer_upcard': dealer_upcard,
        'dealer_total': dealer_total,
        'dealer_soft': dealer_soft,
        'advice': advice,
        'entry_recommendation': entry,
        'insurance': insurance,
        'session': session_data,
    }
