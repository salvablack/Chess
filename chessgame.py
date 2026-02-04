# chess_pgn_viewer_streamlit.py
import streamlit as st
import chess
import chess.pgn
import io

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Chess PGN Viewer",
    page_icon="♟️",
    layout="wide"
)

HIGHLIGHT_FROM = "#f7ec6e"
HIGHLIGHT_TO = "#f1c40f"

# ---------------- SVG CON ANIMACIÓN ----------------
def board_svg(board, last_move=None):
    svg = board._repr_svg_()

    if last_move:
        from_sq = chess.square_name(last_move.from_square)
        to_sq = chess.square_name(last_move.to_square)

        style = f"""
        <style>
        .square-{from_sq}, .square-{to_sq} {{
            transition: fill 0.4s ease-in-out;
        }}
        .square-{from_sq} {{ fill: {HIGHLIGHT_FROM} !important; }}
        .square-{to_sq} {{ fill: {HIGHLIGHT_TO} !important; }}
        </style>
        """
        svg = svg.replace("</svg>", style + "</svg>")

    return svg

# ---------------- APP ----------------
def main():
    st.title("♟️ RedRock Chess PGN")

    # ----------- STATE -----------
    defaults = {
        "games": [],
        "current_game_index": 0,
        "current_move_index": 0,
        "board": chess.Board(),
        "moves": [],
        "last_uploaded_file": None,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ---------------- SIDEBAR ----------------
    with st.sidebar:
        uploaded_file = st.file_uploader("Cargar archivo PGN", type=["pgn"])

        if uploaded_file and uploaded_file != st.session_state.last_uploaded_file:
            pgn_io = io.StringIO(uploaded_file.read().decode("utf-8"))

            games = []
            while (game := chess.pgn.read_game(pgn_io)) is not None:
                games.append(game)

            if games:
                st.session_state.games = games
                st.session_state.current_game_index = 0
                st.session_state.current_move_index = 0
                st.session_state.last_uploaded_file = uploaded_file

                game = games[0]
                st.session_state.board = game.board()
                st.session_state.moves = list(game.mainline_moves())
                st.rerun()

        if st.session_state.games:
            options = [
                f"{i+1}. {g.headers.get('White')} – {g.headers.get('Black')}"
                for i, g in enumerate(st.session_state.games)
            ]
            selected = st.selectbox("Seleccionar partida", options)
            new_index = int(selected.split(".")[0]) - 1

            if new_index != st.session_state.current_game_index:
                st.session_state.current_game_index = new_index
                st.session_state.current_move_index = 0
                game = st.session_state.games[new_index]
                st.session_state.board = game.board()
                st.session_state.moves = list(game.mainline_moves())
                st.rerun()

    # ---------------- INFO + CONTROLES ----------------
    if st.session_state.games:
        game = st.session_state.games[st.session_state.current_game_index]

        st.markdown(
            f"**{game.headers.get('White')}** vs **{game.headers.get('Black')}  \n"
            f"*{game.headers.get('Event','')}*"
        )

        c1, c2, c3, c4, c5 = st.columns([1, 1, 2, 1, 1])

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

    # ----------- TABLERO ANIMADO -----------
    with col1:
        if st.session_state.games:
            board = st.session_state.board.copy()
            last_move = None

            for i, move in enumerate(
                st.session_state.moves[:st.session_state.current_move_index]
            ):
                board.push(move)
                last_move = move

            st.markdown(
                board_svg(board, last_move),
                unsafe_allow_html=True
            )

    # ----------- MOVIMIENTOS PROGRESIVOS -----------
    with col2:
        st.subheader("Movimientos")

        if st.session_state.current_move_index == 0:
            st.info("Avanza la partida para ver los movimientos")
        else:
            temp = chess.Board()
            lines = []

            for i, move in enumerate(
                st.session_state.moves[:st.session_state.current_move_index]
            ):
                san = temp.san(move)
                move_no = i // 2 + 1
                text = f"{move_no}. {san}" if i % 2 == 0 else san
                lines.append(text)
                temp.push(move)

            st.markdown("\n".join(lines))


if __name__ == "__main__":
    main()



