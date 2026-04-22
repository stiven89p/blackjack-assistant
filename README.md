# Blackjack Assistant

Asistente de blackjack en tiempo real con conteo de cartas Hi-Lo, estrategia básica perfecta y seguimiento de sesión con bankroll.

## Características

- **Conteo Hi-Lo** — Lleva el Running Count y el True Count automáticamente conforme se ingresan cartas.
- **Estrategia básica perfecta** — Recomienda la jugada óptima (Hit, Stand, Double, Split, Surrender) para cada situación usando tablas de estrategia para manos duras, blandas y pares.
- **Recomendación de entrada** — Indica si conviene jugar la ronda según el True Count actual.
- **Soporte de splits** — Maneja múltiples manos después de separar un par.
- **Undo** — Deshace la última acción registrada.
- **Historial de sesión** — Registra bankroll, apuestas sugeridas y cartas de cada ronda con seguimiento de ganancias/pérdidas.

## Requisitos

- Python 3.9+
- pip

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
uvicorn main:app --reload
```

Abre el navegador en `http://localhost:8000`.

## Flujo de juego

1. Selecciona el número de mazos al iniciar.
2. Ingresa las cartas usando los botones o el teclado conforme se reparten.
3. Cambia entre fases con las pestañas **MI MANO / OTROS / DEALER** (o teclas `M`, `O`, `D`).
4. El asistente recomienda la jugada en tiempo real.
5. Presiona **Nueva ronda** al terminar; el conteo se conserva entre rondas.
6. Presiona **Nuevo mazo** para resetear todo el conteo.

### Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `A` | As |
| `2`–`9` | Cartas 2 a 9 |
| `0` / `T` | 10 |
| `J` `Q` `K` | Figuras |
| `M` | Cambiar a Mi mano |
| `O` | Cambiar a Otros jugadores |
| `D` | Cambiar a Dealer |
| `Z` | Deshacer |
| `N` | Nueva ronda |

## Historial de sesión

1. Completa el formulario en la sección **Historial de Sesión** con el bankroll inicial y los límites de apuesta.
2. El sistema sugiere la apuesta óptima por ronda según el True Count (spread 1×–2×–4×–8× la apuesta mínima).
3. Al presionar **Nueva ronda**, se archivan las cartas de esa ronda.
4. Registra el resultado (Ganar / Push / Perder) para actualizar el bankroll automáticamente.

## Estructura del proyecto

```
blackjack-assistant/
├── main.py          # API FastAPI — endpoints y estado de sesión
├── blackjack.py     # Lógica: conteo Hi-Lo, tablas de estrategia, recomendaciones
├── index.html       # Frontend SPA (HTML + CSS + JS vanilla)
└── requirements.txt # Dependencias Python
```

## Stack técnico

- **Backend:** FastAPI + Uvicorn
- **Frontend:** HTML5 / CSS3 / JavaScript vanilla (sin dependencias externas)
- **Estado:** En memoria por sesión (sin base de datos)
