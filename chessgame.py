# chess_pgn_viewer_streamlit.py
import streamlit as st
import chess
import chess.pgn
import io

# ---------------- CONFIGURACIÓN DE PÁGINA ----------------
st.set_page_config(
    page_title="Chess PGN Viewer - Multi-Partida",
    page_icon="♟️",
    layout="wide"
)

# ---------------- FUNCIONES AUXILIARES ----------------

def create_chess_board_svg(board: chess.Board):
    """Devuelve el SVG del tablero"""
    return board._repr_svg_()

# ---------------- APP PRINCIPAL ----------------

def main():
    st.title("♟️ Visor de Partidas PGN - Multi-Partida")
    st.markdown("Carga un archivo PGN y revisa las partidas con animación y controles")

    # ----------- ESTADO DE SESIÓN -----------
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
    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

    # ---------------- SIDEBAR ----------------
    with st.sidebar:
        st.header("Controles")

        uploaded_file = st.file_uploader("Cargar archivo PGN", type=["pgn"])

        # ----------- CARGA DEL PGN -----------
        if uploaded_file and uploaded_file != st.session_state.last_uploaded_file:
            with st.spinner("Leyendo archivo PGN..."):
                try:
                    pgn_text = uploaded_file.read().decode("utf-8")
                    pgn_io = io.StringIO(pgn_text)

                    games = []
                    while True:
                        game = chess.pgn.read_game(pgn_io)
                        if game is None:
                            break
                        games.append(game)

                    if not games:
                        st.error("No se encontraron partidas en el archivo.")
                        return

                    # Guardamos estado
                    st.session_state.games = games
                    st.session_state.current_game_index = 0
                    st.session_state.current_move_index = 0
                    st.session_state.last_uploaded_file = uploaded_file

                    # 🔑 INICIALIZAR PRIMERA PARTIDA
                    first_game = games[0]
                    st.session_state.board = first_game.board()
                    st.session_state.moves = list(first_game.mainline_moves())

                    st.success(f"¡Cargadas {len(games)} partidas!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al leer el PGN: {e}")

        st.markdown("---")

        # ----------- INFO DE PARTIDA ACTUAL -----------
        if st.session_state.games:
            game = st.session_state.games[st.session_state.current_game_index]
            st.markdown(
                f"""
                **Partida:** {st.session_state.current_game_index + 1} / {len(st.session_state.games)}  
                **Blancas:** {game.headers.get("White", "?")}  
                **Negras:** {game.headers.get("Black", "?")}  
                *{game.headers.get("Event", "")}*
                """
            )

        st.markdown("---")

        # ----------- SELECTOR DE PARTIDA -----------
        if st.session_state.games:
            options = [
                f"{i+1}. {g.headers.get('White','?')} – {g.headers.get('Black','?')}"
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

    # ---------------- CONTENIDO PRINCIPAL ----------------
    col1, col2 = st.columns([3, 2])

    # ----------- TABLERO -----------
    with col1:
        st.subheader("Tablero")

        if st.session_state.games and st.session_state.moves:
            board = st.session_state.board.copy()

            for move in st.session_state.moves[:st.session_state.current_move_index]:
                board.push(move)

            st.markdown(create_chess_board_svg(board), unsafe_allow_html=True)

        else:
            st.info("Carga un archivo PGN para comenzar")

    # ----------- MOVIMIENTOS -----------
    with col2:
        st.subheader("Movimientos")

        if st.session_state.moves:
            temp_board = chess.Board()
            lines = []

            for i, move in enumerate(st.session_state.moves):
                san = temp_board.san(move)
                move_no = i // 2 + 1

                text = f"{move_no}. {san}" if i % 2 == 0 else san
                if i == st.session_state.current_move_index - 1:
                    text = f"👉 **{text}**"

                lines.append(text)
                temp_board.push(move)

            st.markdown("\n".join(lines))
        else:
            st.info("No hay movimientos cargados")

    # ---------------- CONTROLES ----------------
    if st.session_state.games and st.session_state.moves:
        st.markdown("---")
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


if __name__ == "__main__":
    main()

