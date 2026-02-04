import streamlit as st
import chess
import chess.pgn
import io
from stockfish import Stockfish

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Chess PGN Analyzer",
    page_icon="♟️",
    layout="wide"
)

HIGHLIGHT_FROM = "#f7ec6e"
HIGHLIGHT_TO = "#f1c40f"

# ---------------- ENGINE ----------------
@st.cache_resource
def load_engine():
    # Cambia esta ruta si tu ejecutable está en otro lugar
    stockfish_path = "./stockfish/src/stockfish"  
    return Stockfish(
        path=stockfish_path,
        parameters={
            "Threads": 2,
            "Minimum Thinking Time": 30
        }
    )

def explain_eval(cp):
    if cp > 150:
        return "Las blancas tienen clara ventaja."
    if cp > 50:
        return "Las blancas están ligeramente mejor."
    if cp > -50:
        return "La posición está equilibrada."
    if cp > -150:
        return "Las negras están ligeramente mejor."
    return "Las negras tienen clara ventaja."

def analyze_position(board, engine):
    engine.set_fen_position(board.fen())
    ev = engine.get_evaluation()

    if ev["type"] == "mate":
        return f"Mate en {ev['value']}", "⚠️ Posición decisiva"

    cp = ev["value"]
    return f"{cp/100:.2f}", explain_eval(cp)

# ---------------- SVG TABLERO ----------------
def board_svg(board, last_move=None):
    svg = board._repr_svg_()

    if last_move:
        f = chess.square_name(last_move.from_square)
        t = chess.square_name(last_move.to_square)

        style = f"""
        <style>
        .square-{f}, .square-{t} {{
            transition: fill 0.4s ease-in-out;
        }}
        .square-{f} {{ fill: {HIGHLIGHT_FROM} !important; }}
        .square-{t} {{ fill: {HIGHLIGHT_TO} !important; }}
        </style>
        """
        svg = svg.replace("</svg>", style + "</svg>")

    return svg

# ---------------- APP ----------------
def main():
    st.title("♟️ Visor y Analizador de Partidas")

    engine = load_engine()

    # ----------- STATE -----------
    for k, v in {
        "games": [],
        "current_game_index": 0,
        "current_move_index": 0,
        "moves": [],
        "last_uploaded_file": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ---------------- SIDEBAR ----------------
    with st.sidebar:
        uploaded = st.file_uploader("Cargar PGN", type=["pgn"])

        if uploaded and uploaded != st.session_state.last_uploaded_file:
            pgn_io = io.StringIO(uploaded.read().decode("utf-8"))

            games = []
            while (g := chess.pgn.read_game(pgn_io)) is not None:
                games.append(g)

            if games:
                st.session_state.games = games
                st.session_state.current_game_index = 0
                st.session_state.current_move_index = 0
                st.session_state.moves = list(games[0].mainline_moves())
                st.session_state.last_uploaded_file = uploaded
                st.rerun()

        if st.session_state.games:
            options = [
                f"{i+1}. {g.headers.get('White')} – {g.headers.get('Black')}"
                for i, g in enumerate(st.session_state.games)
            ]
            selected = st.selectbox("Seleccionar partida", options)
            idx = int(selected.split(".")[0]) - 1

            if idx != st.session_state.current_game_index:
                st.session_state.current_game_index = idx
                st.session_state.current_move_index = 0
                st.session_state.moves = list(
                    st.session_state.games[idx].mainline_moves()
                )
                st.rerun()

    # ---------------- INFO + CONTROLES ----------------
    if st.session_state.games:
        game = st.session_state.games[st.session_state.current_game_index]

        st.markdown(
            f"**{game.headers.get('White')}** vs **{game.headers.get('Black')}**  \n"
            f"*{game.headers.get('Event','')}*"
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            if st.button("⏮️"):
                st.session_state.current_move_index = 0
                st.rerun()
        with c2:
            if st.button("◀️") and st.session_state.current_move_index > 0:
                st.session_state.current_move_index -= 1
                st.rerun()
        with c3:
            st.markdown(
                f"<h4 style='text-align:center;'>"
                f"{st.session_state.current_move_index} / {len(st.session_state.moves)}"
                f"</h4>",
                unsafe_allow_html=True
            )
        with c4:
            if st.button("▶️") and st.session_state.current_move_index < len(st.session_state.moves):
                st.session_state.current_move_index += 1
                st.rerun()
        with c5:
            if st.button("⏭️"):
                st.session_state.current_move_index = len(st.session_state.moves)
                st.rerun()

        st.markdown("---")

    # ---------------- CONTENIDO ----------------
    col1, col2 = st.columns([3, 2])

    # ----------- TABLERO + ANÁLISIS -----------
    with col1:
        board = chess.Board()
        last_move = None

        for m in st.session_state.moves[:st.session_state.current_move_index]:
            board.push(m)
            last_move = m

        st.markdown(board_svg(board, last_move), unsafe_allow_html=True)

        if last_move:
            eval_text, eval_expl = analyze_position(board, engine)
            st.markdown("### 🧠 Análisis del movimiento")
            st.write(eval_expl)
            st.write(f"**Evaluación:** {eval_text}")

    # ----------- MOVIMIENTOS PROGRESIVOS -----------
    with col2:
        st.subheader("Movimientos")

        temp = chess.Board()
        for i, m in enumerate(st.session_state.moves[:st.session_state.current_move_index]):
            san = temp.san(m)
            move_no = i // 2 + 1
            st.write(f"{move_no}. {san}" if i % 2 == 0 else san)
            temp.push(m)


if __name__ == "__main__":
    main()


