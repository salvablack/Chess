# chess_pgn_viewer_streamlit.py
import streamlit as st
import chess
import chess.pgn
import io
from pathlib import Path

# Configuración inicial de la página
st.set_page_config(
    page_title="Chess PGN Viewer - Multi-Partida",
    page_icon="♟️",
    layout="wide"
)

# ---------------- ESTILOS Y CONSTANTES ----------------
UNICODE_PIECES = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚"
}

SQUARE_SIZE = 60
BOARD_PIXEL = SQUARE_SIZE * 8

HIGHLIGHT_FROM = "#f7ec6e"
HIGHLIGHT_TO = "#f1c40f"
OVERLAY_COLOR = "#ccbe00"

# Colores del tablero
LIGHT_SQUARE = "#e9d2ee"
DARK_SQUARE = "#7d1336"

# ---------------- FUNCIONES AUXILIARES ----------------

def square_to_coord(square):
    """Convierte número de casilla (0-63) a coordenadas pixel"""
    file = chess.square_file(square)
    rank = 7 - chess.square_rank(square)
    x = file * SQUARE_SIZE
    y = rank * SQUARE_SIZE
    return x, y


def create_chess_board_svg(board: chess.Board, highlight_from=None, highlight_to=None):
    """Genera el SVG del tablero con posibles resaltados"""
    svg = board._repr_svg_()
    
    # Si queremos resaltar casillas, podemos inyectar estilos (más complejo)
    # Por simplicidad, usaremos el SVG por defecto + texto superpuesto después
    return svg


def get_move_san(board, move):
    return board.san(move)


def main():
    st.title("♟️ Visor de Partidas PGN - Multi-Partida")
    st.markdown("Carga un archivo PGN y revisa las partidas con animación y controles")

    # Estado de la sesión
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
    if "show_origin_square" not in st.session_state:
        st.session_state.show_origin_square = True

    # ------------------- BARRA LATERAL -------------------
    with st.sidebar:
        st.header("Controles")
        
        uploaded_file = st.file_uploader("Cargar archivo PGN", type=["pgn"])

        if uploaded_file is not None and uploaded_file != st.session_state.get("last_uploaded_file"):
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
                    
                    st.session_state.games = games
                    st.session_state.current_game_index = 0
                    st.session_state.current_move_index = 0
                    st.session_state.last_uploaded_file = uploaded_file
                    
                    if games:
                        st.success(f"¡Cargadas {len(games)} partidas!")
                    else:
                        st.error("No se encontraron partidas en el archivo.")
                except Exception as e:
                    st.error(f"Error al leer el PGN: {e}")

        st.markdown("---")

        # Información de la partida actual
        if st.session_state.games:
            game = st.session_state.games[st.session_state.current_game_index]
            white = game.headers.get("White", "?")
            black = game.headers.get("Black", "?")
            event = game.headers.get("Event", "Sin evento")
            
            st.markdown(f"**Partida actual**: {st.session_state.current_game_index + 1} / {len(st.session_state.games)}")
            st.markdown(f"**{white}**  —  **{black}**")
            st.markdown(f"*{event}*")

        st.markdown("---")

        # Selector de partida
        if st.session_state.games:
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
                st.rerun()

        st.markdown("---")

        # Mostrar origen
        show_origin = st.checkbox("Mostrar casilla de origen", value=st.session_state.show_origin_square)
        st.session_state.show_origin_square = show_origin

    # ------------------- CONTENIDO PRINCIPAL -------------------
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Tablero")

        if st.session_state.games and st.session_state.moves:
            board = st.session_state.board.copy()
            current_move_index = st.session_state.current_move_index

            # Aplicamos los movimientos hasta el índice actual
            for move in st.session_state.moves[:current_move_index]:
                board.push(move)

            # Mostramos el tablero
            st.markdown(
                create_chess_board_svg(board),
                unsafe_allow_html=True
            )

            # Información adicional sobre el movimiento actual
            if current_move_index > 0:
                last_move = st.session_state.moves[current_move_index - 1]
                san = board.san(last_move) if current_move_index == len(st.session_state.moves) else ""
                st.caption(f"Último movimiento: {san}  •  {chess.square_name(last_move.from_square)} → {chess.square_name(last_move.to_square)}")
        else:
            st.info("Carga un archivo PGN para comenzar")

    with col2:
        st.subheader("Movimientos")

        if st.session_state.moves:
            moves_text = []
            temp_board = chess.Board()
            for i, move in enumerate(st.session_state.moves):
                san = temp_board.san(move)
                move_num = (i // 2) + 1
                if i % 2 == 0:
                    moves_text.append(f"{move_num}. **{san}**")
                else:
                    moves_text.append(f"{san}")
                temp_board.push(move)

            # Resaltamos el movimiento actual
            current = st.session_state.current_move_index - 1
            if current >= 0:
                moves_text[current] = f"→ {moves_text[current]} ←"

            st.markdown("\n".join(moves_text), unsafe_allow_html=True)
        else:
            st.info("No hay movimientos cargados")

    # ------------------- CONTROLES DE NAVEGACIÓN -------------------
    if st.session_state.games and st.session_state.moves:
        st.markdown("---")
        cols = st.columns([1, 1, 2, 1, 1])

        with cols[0]:
            if st.button("⏮️ Primera"):
                st.session_state.current_move_index = 0
                st.rerun()

        with cols[1]:
            if st.button("◀️ Anterior"):
                if st.session_state.current_move_index > 0:
                    st.session_state.current_move_index -= 1
                    st.rerun()
                elif st.session_state.current_game_index > 0:
                    st.session_state.current_game_index -= 1
                    st.session_state.current_move_index = 0
                    st.rerun()

        with cols[2]:
            st.markdown(
                f"<h3 style='text-align:center;'>Movimiento {st.session_state.current_move_index} / {len(st.session_state.moves)}</h3>",
                unsafe_allow_html=True
            )

        with cols[3]:
            if st.button("Siguiente ▶️"):
                if st.session_state.current_move_index < len(st.session_state.moves):
                    st.session_state.current_move_index += 1
                    st.rerun()
                elif st.session_state.current_game_index < len(st.session_state.games) - 1:
                    st.session_state.current_game_index += 1
                    st.session_state.current_move_index = 0
                    st.rerun()

        with cols[4]:
            if st.button("⏭️ Última"):
                st.session_state.current_move_index = len(st.session_state.moves)
                st.rerun()


if __name__ == "__main__":
    main()
