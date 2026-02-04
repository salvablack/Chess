import streamlit as st
import chess
import chess.pgn
import io
import requests

# ---------------- CONFIGURACIÓN ----------------
st.set_page_config(
    page_title="♟️ Visor y Analizador de Partidas PGN",
    page_icon="♟️",
    layout="wide"
)

# ---------------- FUNCIONES ----------------
def get_lichess_analysis(fen):
    """Consulta la evaluación en Lichess API usando la posición FEN"""
    url = "https://lichess.org/api/cloud-eval"
    params = {"fen": fen}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def create_board_svg(board):
    """Genera SVG del tablero"""
    return board._repr_svg_()

# ---------------- APP ----------------
def main():
    st.title("♟️ Visor y Analizador de Partidas PGN")
    st.markdown("Carga un archivo PGN y revisa partidas con análisis en tiempo real.")

    # ---------------- SESIÓN ----------------
    if "games" not in st.session_state:
        st.session_state.games = []
    if "current_game_index" not in st.session_state:
        st.session_state.current_game_index = 0
    if "current_move_index" not in st.session_state:
        st.session_state.current_move_index = 0
    if "board" not in st.session_state:
        st.session_state.board = chess.Board()
    if "moves" not in st.session_state:
        st.session_state.moves = []

    # ---------------- SIDEBAR ----------------
    with st.sidebar:
        st.header("Controles")
        uploaded_file = st.file_uploader("Cargar archivo PGN", type=["pgn"])

        if uploaded_file is not None and uploaded_file != st.session_state.get("last_uploaded_file"):
            pgn_text = uploaded_file.read().decode("utf-8")
            pgn_io = io.StringIO(pgn_text)

            games = []
            while True:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break
                games.append(game)

            if games:
                st.session_state.games = games
                st.session_state.current_game_index = 0
                st.session_state.current_move_index = 0
                st.session_state.board = games[0].board()
                st.session_state.moves = list(games[0].mainline_moves())
                st.session_state.last_uploaded_file = uploaded_file
                st.success(f"¡Cargadas {len(games)} partidas!")
            else:
                st.error("No se encontraron partidas en el archivo.")

        if st.session_state.games:
            game = st.session_state.games[st.session_state.current_game_index]
            white = game.headers.get("White", "?")
            black = game.headers.get("Black", "?")
            event = game.headers.get("Event", "Sin evento")

            st.markdown(f"**Partida actual:** {st.session_state.current_game_index + 1} / {len(st.session_state.games)}")
            st.markdown(f"**{white}** vs **{black}**")
            st.markdown(f"*{event}*")

            # Selector de partida
            game_options = []
            for i, g in enumerate(st.session_state.games):
                w = g.headers.get("White", "?")
                b = g.headers.get("Black", "?")
                e = g.headers.get("Event", "")[:40]
                game_options.append(f"{i+1}. {w} – {b} ({e})")

            selected = st.selectbox("Seleccionar partida", game_options)
            new_index = int(selected.split(".")[0]) - 1
            if new_index != st.session_state.current_game_index:
                st.session_state.current_game_index = new_index
                st.session_state.current_move_index = 0
                game = st.session_state.games[new_index]
                st.session_state.board = game.board()
                st.session_state.moves = list(game.mainline_moves())

    # ---------------- CONTROLES DE MOVIMIENTO ----------------
    if st.session_state.games and st.session_state.moves:
        cols = st.columns([1, 1, 2, 1, 1])
        with cols[0]:
            if st.button("⏮️ Primera"):
                st.session_state.current_move_index = 0
        with cols[1]:
            if st.button("◀️ Anterior"):
                if st.session_state.current_move_index > 0:
                    st.session_state.current_move_index -= 1
        with cols[2]:
            st.markdown(f"### Movimiento {st.session_state.current_move_index} / {len(st.session_state.moves)}", unsafe_allow_html=True)
        with cols[3]:
            if st.button("Siguiente ▶️"):
                if st.session_state.current_move_index < len(st.session_state.moves):
                    st.session_state.current_move_index += 1
        with cols[4]:
            if st.button("⏭️ Última"):
                st.session_state.current_move_index = len(st.session_state.moves)

    # ---------------- TABLERO Y ANALISIS ----------------
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Tablero")
        if st.session_state.games and st.session_state.moves:
            board = st.session_state.board.copy()
            for move in st.session_state.moves[:st.session_state.current_move_index]:
                board.push(move)
            st.markdown(create_board_svg(board), unsafe_allow_html=True)
        else:
            st.info("Carga un archivo PGN para comenzar.")

    with col2:
        st.subheader("Movimientos y análisis")
        if st.session_state.moves and st.session_state.current_move_index > 0:
            board_temp = st.session_state.board.copy()
            moves_text = []
            for i, move in enumerate(st.session_state.moves[:st.session_state.current_move_index]):
                san = board_temp.san(move)
                move_num = (i // 2) + 1
                if i % 2 == 0:
                    moves_text.append(f"{move_num}. **{san}**")
                else:
                    moves_text.append(san)
                board_temp.push(move)
            st.markdown("\n".join(moves_text), unsafe_allow_html=True)

            # Analisis en tiempo real con Lichess API
            fen = board_temp.fen()
            analysis = get_lichess_analysis(fen)
            if analysis and "pvs" in analysis:
                best_move = analysis["pvs"][0]["moves"].split()[0]
                score = analysis["pvs"][0].get("cp")
                mate = analysis["pvs"][0].get("mate")
                if mate is not None:
                    score_text = f"Jaque mate en {mate} movimientos"
                elif score is not None:
                    score_text = f"Evaluación: {score / 100:.2f}"
                else:
                    score_text = "Evaluación no disponible"

                st.markdown(f"**Mejor movimiento según Stockfish:** {best_move}")
                st.markdown(f"**{score_text}**")
            else:
                st.markdown("_Análisis no disponible en este momento._")
        else:
            st.info("Avanza movimientos para ver análisis.")

if __name__ == "__main__":
    main()

