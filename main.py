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
}


class SetupRequest(BaseModel):
    num_decks: int


class CardRequest(BaseModel):
    card: str
    target: str  # 'mine' | 'dealer' | 'other'


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

    state['running_count'] += bj.HILO_VALUES[req.card]
    state['cards_seen'] += 1
    state['history'].append({
        'action': 'card',
        'card': req.card,
        'target': req.target,
        'hand_index': state['active_hand'],
    })

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

    advice = bj.get_advice(active_hand, dealer_upcard)
    entry = bj.get_entry_recommendation(tc)

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
    }
