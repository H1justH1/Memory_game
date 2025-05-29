import streamlit as st
import random
import time
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import base64

st.set_page_config(page_title="🃏 Card Memory Game", layout="wide")

# Malaysia Time
def malaysia_time():
    return datetime.utcnow() + timedelta(hours=8)

# Leaderboard file
LEADERBOARD_FILE = "leaderboard.csv"

# Sound effect functions
def generate_tone(frequency, duration=0.2, sample_rate=22050):
    """Generate a simple tone for sound effects"""
    import numpy as np
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave = np.sin(2 * np.pi * frequency * t) * 0.3
    return wave

def create_audio_data(wave, sample_rate=22050):
    """Convert wave to base64 audio data"""
    try:
        import numpy as np
        import io
        from scipy.io.wavfile import write
        
        # Convert to 16-bit PCM
        audio_data = (wave * 32767).astype(np.int16)
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        write(buffer, sample_rate, audio_data)
        buffer.seek(0)
        
        # Convert to base64
        audio_b64 = base64.b64encode(buffer.read()).decode()
        return f"data:audio/wav;base64,{audio_b64}"
    except ImportError:
        return None

# Load or create leaderboard with caching
@st.cache_data
def load_leaderboard():
    try:
        return pd.read_csv(LEADERBOARD_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Name", "Difficulty", "Moves", "Date"])

def save_leaderboard(leaderboard):
    leaderboard.to_csv(LEADERBOARD_FILE, index=False)
    load_leaderboard.clear()

# Sidebar inputs
st.sidebar.title("🧩 Login & Settings")

# Sound settings
sound_enabled = st.sidebar.checkbox("🔊 Sound Effects", value=True)

# Multiplayer or solo
mode = st.sidebar.radio("Game Mode", ["Solo", "Multiplayer"], horizontal=True)

if mode == "Solo":
    player_names = [st.sidebar.text_input("Your name", key="solo_name")]
else:
    num_players = st.sidebar.slider("Number of Players", 2, 4, 2)
    player_names = []
    for i in range(num_players):
        player_names.append(st.sidebar.text_input(f"Player {i+1} name", key=f"player_{i}"))

difficulty = st.sidebar.selectbox("Difficulty level", ["Easy (2x2)", "Medium (4x4)", "Hard (6x6)"])
theme = st.sidebar.radio("🎨 Theme Mode", ["Light", "Dark"], horizontal=True)
difficulty_map = {"Easy (2x2)": (2, 2), "Medium (4x4)": (4, 4), "Hard (6x6)": (6, 6)}
rows, cols = difficulty_map[difficulty]

# Enhanced CSS with animations and mobile responsiveness - CONSISTENT CARD SIZES
css_styles = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

body {{
    font-family: 'Poppins', sans-serif;
    background: {'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' if theme == 'Dark' else 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)'};
}}

[data-testid="stSidebar"] {{
    background: {'linear-gradient(180deg, #1e293b 0%, #334155 100%) !important' if theme == 'Dark' else 'linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%) !important'};
    color: {'white' if theme == 'Dark' else 'black'} !important;
}}

/* Base card styling for ALL cards - consistent sizing */
.card-button, [data-testid="baseButton-secondary"] {{
    background: {'linear-gradient(145deg, #1e293b, #334155) !important' if theme == 'Dark' else 'linear-gradient(145deg, #ffffff, #f1f5f9) !important'};
    color: {'#f1f5f9 !important' if theme == 'Dark' else '#1e293b !important'};
    border: {'2px solid #475569 !important' if theme == 'Dark' else '2px solid #cbd5e1 !important'};
    border-radius: 15px !important;
    font-size: clamp(3rem, 6vw, 6rem) !important;
    height: clamp(100px, 20vw, 180px) !important;
    width: 100% !important;
    margin: 8px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: {'0 6px 20px rgba(0,0,0,0.3) !important' if theme == 'Dark' else '0 6px 20px rgba(0,0,0,0.1) !important'};
    position: relative !important;
    overflow: hidden !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-weight: 600 !important;
    font-family: 'Poppins', sans-serif !important;
    min-height: clamp(100px, 20vw, 180px) !important;
    max-height: clamp(100px, 20vw, 180px) !important;
}}

/* Hover effects for all cards */
.card-button:hover, [data-testid="baseButton-secondary"]:hover:not(:disabled) {{
    transform: translateY(-5px) scale(1.02) !important;
    box-shadow: {'0 10px 30px rgba(0,0,0,0.4) !important' if theme == 'Dark' else '0 10px 30px rgba(0,0,0,0.15) !important'};
}}

/* Active state for all cards */
.card-button:active, [data-testid="baseButton-secondary"]:active {{
    transform: translateY(-2px) scale(0.98) !important;
}}

/* Disabled state styling */
[data-testid="baseButton-secondary"]:disabled {{
    opacity: 1 !important;
    cursor: default !important;
}}

/* Flip animation */
.card-flip {{
    animation: flipCard 0.6s ease-in-out !important;
    font-size: clamp(3rem, 6vw, 6rem) !important;
    height: clamp(100px, 20vw, 180px) !important;
}}

@keyframes flipCard {{
    0% {{ transform: rotateY(0deg) scale(1); }}
    50% {{ transform: rotateY(90deg) scale(1.1); }}
    100% {{ transform: rotateY(0deg) scale(1); }}
}}

/* Match animation */
.card-match {{
    animation: matchPulse 0.8s ease-in-out !important;
    background: linear-gradient(145deg, #10b981, #059669) !important;
    color: white !important;
    font-size: clamp(3rem, 6vw, 6rem) !important;
    height: clamp(100px, 20vw, 180px) !important;
}}

@keyframes matchPulse {{
    0%, 100% {{ transform: scale(1); }}
    50% {{ transform: scale(1.1); box-shadow: 0 0 25px rgba(16, 185, 129, 0.6); }}
}}

/* Unflipped card specific styling */
.card-unflipped {{
    background: {'linear-gradient(145deg, #374151, #4b5563) !important' if theme == 'Dark' else 'linear-gradient(145deg, #e5e7eb, #d1d5db) !important'};
    color: {'#9ca3af !important' if theme == 'Dark' else '#6b7280 !important'};
    border: {'2px solid #6b7280 !important' if theme == 'Dark' else '2px solid #9ca3af !important'};
}}

.card-unflipped:hover:not(:disabled) {{
    background: {'linear-gradient(145deg, #4b5563, #6b7280) !important' if theme == 'Dark' else 'linear-gradient(145deg, #d1d5db, #b5b5b5) !important'};
    transform: translateY(-5px) scale(1.02) !important;
    box-shadow: {'0 10px 30px rgba(0,0,0,0.4) !important' if theme == 'Dark' else '0 10px 30px rgba(0,0,0,0.15) !important'};
}}

.progress-container {{
    width: 100%;
    height: 20px;
    background: {'rgba(51, 65, 85, 0.3)' if theme == 'Dark' else 'rgba(203, 213, 225, 0.5)'};
    border-radius: 10px;
    overflow: hidden;
    margin: 10px 0;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}}

.progress-bar {{
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #1d4ed8);
    border-radius: 10px;
    transition: width 0.5s ease-in-out;
    position: relative;
    overflow: hidden;
}}

.progress-bar::after {{
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 2s infinite;
}}

@keyframes shimmer {{
    0% {{ left: -100%; }}
    100% {{ left: 100%; }}
}}

.stats-card {{
    background: {'rgba(30, 41, 59, 0.8)' if theme == 'Dark' else 'rgba(255, 255, 255, 0.8)'};
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 20px;
    margin: 10px 0;
    border: {'1px solid rgba(71, 85, 105, 0.3)' if theme == 'Dark' else '1px solid rgba(203, 213, 225, 0.3)'};
    box-shadow: {'0 8px 32px rgba(0,0,0,0.3)' if theme == 'Dark' else '0 8px 32px rgba(0,0,0,0.1)'};
}}

/* Mobile responsiveness - maintaining consistent larger sizes */
@media (max-width: 768px) {{
    .card-button, [data-testid="baseButton-secondary"], .card-flip, .card-match {{
        font-size: clamp(2.5rem, 8vw, 4rem) !important;
        height: clamp(80px, 20vw, 120px) !important;
        min-height: clamp(80px, 20vw, 120px) !important;
        max-height: clamp(80px, 20vw, 120px) !important;
        margin: 6px !important;
    }}
    
    .stats-card {{
        padding: 15px;
        margin: 5px 0;
    }}
}}

@media (max-width: 480px) {{
    .card-button, [data-testid="baseButton-secondary"], .card-flip, .card-match {{
        font-size: clamp(2rem, 10vw, 3rem) !important;
        height: clamp(70px, 22vw, 100px) !important;
        min-height: clamp(70px, 22vw, 100px) !important;
        max-height: clamp(70px, 22vw, 100px) !important;
        margin: 4px !important;
    }}
}}

/* Hide default button focus outline */
[data-testid="baseButton-secondary"]:focus {{
    outline: none !important;
    box-shadow: {'0 6px 20px rgba(0,0,0,0.3) !important' if theme == 'Dark' else '0 6px 20px rgba(0,0,0,0.1) !important'};
}}
</style>
"""

st.markdown(css_styles, unsafe_allow_html=True)

EMOJIS = ['🐶','🐱','🐭','🦊','🐻','🐼','🐨','🐯','🐸','🐵','🐔','🐧','🐴','🦄','🐝','🐢','🐙','🦋']

def init_game(rows, cols, player_names):
    num_pairs = (rows * cols) // 2
    deck = EMOJIS[:num_pairs] * 2
    random.shuffle(deck)
    return {
        "deck": deck,
        "flipped": [False] * (rows * cols),
        "matched": [False] * (rows * cols),
        "first_choice": None,
        "second_choice": None,
        "moves": 0,
        "score": 0,
        "waiting": False,
        "wait_start": None,
        "start_time": None,
        "rows": rows,
        "cols": cols,
        "num_pairs": num_pairs,
        "game_over": False,
        "mode": mode,
        "player_names": player_names,
        "current_player": 0,
        "player_scores": [0]*len(player_names),
        "score_submitted": False,
        "last_match": False,
        "game_just_completed": False,
    }

def game_params_changed(game, rows, cols, player_names, mode):
    return (game.get("rows") != rows or
            game.get("cols") != cols or
            game.get("player_names") != player_names or
            game.get("mode") != mode)

# Initialize game state
if "game" not in st.session_state:
    st.session_state.game = init_game(rows, cols, player_names)

game = st.session_state.game

# Only reinitialize if parameters actually changed
if game_params_changed(game, rows, cols, player_names, mode):
    st.session_state.game = init_game(rows, cols, player_names)
    game = st.session_state.game

# Create containers for dynamic content
header_container = st.container()
progress_container = st.container()
game_board_container = st.container()
status_container = st.container()
sound_container = st.container()

# Reset submit flag if new game started
if game["moves"] == 0 and game.get("score_submitted", False):
    game["score_submitted"] = False

# Handle clear leaderboard
if st.sidebar.button("🗑️ Clear Leaderboard"):
    empty_leaderboard = pd.DataFrame(columns=["Name", "Difficulty", "Moves", "Date"])
    save_leaderboard(empty_leaderboard)
    st.session_state.game = init_game(rows, cols, player_names)
    st.sidebar.success("Leaderboard cleared and game restarted!")
    st.rerun()

# Header
with header_container:
    if mode == "Solo":
        st.markdown(f"# 🃏 Memory Game - Hello, **{player_names[0] if player_names[0] else 'Player'}**!")
    else:
        st.markdown(f"# 🃏 Memory Game - Multiplayer Mode")
    
    # Display game rules
    with st.expander("📜 Game Rules", expanded=False):
        st.markdown("### 🎮 Solo Mode Rules")
        st.markdown("""
        - Flip two cards at a time to find matching pairs.
        - The game ends when all pairs are matched.
        - Your performance is scored by **number of moves**.
        - Try to beat your **personal best** and climb the leaderboard!
        """)

        st.markdown("### 🧑‍🤝‍🧑 Multiplayer Mode Rules")
        st.markdown("""
        - Two or more players take turns flipping two cards.
        - If a player finds a match, they earn a point and take another turn.
        - If the cards don't match, the next player takes their turn.
        - The game ends when all pairs are matched.
        - The player with the **most matched pairs wins**!
        """)

# Progress bar and stats
with progress_container:
    progress_percentage = (game["score"] / game["num_pairs"]) * 100 if game["num_pairs"] > 0 else 0
    
    st.markdown(f'<div class="stats-card">', unsafe_allow_html=True)
    st.markdown(f"### Difficulty: **{difficulty}**")
    
    # Progress bar
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {progress_percentage}%"></div>
    </div>
    <div style="text-align: center; margin-top: 5px; font-weight: 600;">
        Progress: {game["score"]}/{game["num_pairs"]} pairs ({progress_percentage:.1f}%)
    </div>
    """, unsafe_allow_html=True)
    
    if mode == "Solo":
        st.markdown(f"""
        <div style="display: flex; justify-content: space-around; margin-top: 15px; font-weight: 600;">
            <div>🎯 Moves: {game["moves"]}</div>
            <div>✅ Matches: {game["score"]}/{game["num_pairs"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        scores_str = " | ".join(
            f"**{name}**: {score}" for name, score in zip(game["player_names"], game["player_scores"])
        )
        st.markdown(f"""
        <div style="margin-top: 15px;">
            <div style="font-weight: 600; margin-bottom: 10px;">
                🎯 Moves: {game["moves"]} | Current Player: **{game["player_names"][game["current_player"]]}**
            </div>
            <div style="font-weight: 600;">Scores: {scores_str}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Personal best display (cached)
if mode == "Solo" and player_names[0]:
    leaderboard = load_leaderboard()
    personal_best = leaderboard[(leaderboard["Name"] == player_names[0]) & (leaderboard["Difficulty"] == difficulty)]
    if not personal_best.empty:
        best = personal_best.sort_values(by=["Moves", "Date"]).iloc[0]
        st.info(f"🏅 **Your Best:** {best['Moves']} moves on {best['Date']}")

# Handle waiting state with reduced reruns
should_rerun = False
if game["waiting"]:
    st_autorefresh(interval=1000, limit=3, key="auto_refresh")
    if time.time() - game["wait_start"] > 1.5:  # Slightly longer wait for better UX
        f, s = game["first_choice"], game["second_choice"]
        game["flipped"][f] = False
        game["flipped"][s] = False
        game["first_choice"] = game["second_choice"] = None
        game["waiting"] = False
        game["wait_start"] = None
        game["last_match"] = False
        if mode == "Multiplayer":
            game["current_player"] = (game["current_player"] + 1) % len(game["player_names"])
        should_rerun = True

# Game board with enhanced styling - FIXED CARD SIZING
with game_board_container:
    cols_streamlit = st.columns(game["cols"])
    
    for i in range(rows * cols):
        with cols_streamlit[i % cols]:
            if game["matched"][i]:
                # Matched card - show with match styling
                st.markdown(f'<div class="card-button card-match">{game["deck"][i]}</div>', 
                          unsafe_allow_html=True)
                st.button("", key=f"card_{i}", disabled=True, 
                         help=f"Matched card {i+1}: {game['deck'][i]}")
            elif game["flipped"][i]:
                # Flipped card - show with flip animation
                st.markdown(f'<div class="card-button card-flip">{game["deck"][i]}</div>', 
                          unsafe_allow_html=True)
                st.button("", key=f"card_{i}", disabled=True, 
                         help=f"Flipped card {i+1}: {game['deck'][i]}")
            else:
                # Unflipped card - use consistent styling
                if not game["waiting"]:
                    # Add custom CSS class to unflipped cards for consistent styling
                    button_html = f'<div class="card-button card-unflipped">❓</div>'
                    st.markdown(button_html, unsafe_allow_html=True)
                    
                    if st.button("", key=f"card_{i}", help=f"Click to reveal card {i+1}"):
                        # Process card click
                        game["flipped"][i] = True
                        if game["start_time"] is None:
                            game["start_time"] = time.time()
                        
                        if game["first_choice"] is None:
                            game["first_choice"] = i
                            # Sound for first card flip
                            if sound_enabled:
                                match_sound = generate_tone(440, 0.1)  # A4 note
                                if match_sound is not None:
                                    audio_data = create_audio_data(match_sound)
                                    if audio_data:
                                        with sound_container:
                                            st.markdown(f'<audio autoplay><source src="{audio_data}" type="audio/wav"></audio>', 
                                                      unsafe_allow_html=True)
                        else:
                            game["second_choice"] = i
                            game["moves"] += 1
                            f, s = game["first_choice"], game["second_choice"]
                            
                            if game["deck"][f] == game["deck"][s]:
                                # Match found
                                game["matched"][f] = game["matched"][s] = True
                                game["score"] += 1
                                game["last_match"] = True
                                if mode == "Multiplayer":
                                    game["player_scores"][game["current_player"]] += 1
                                game["first_choice"] = game["second_choice"] = None
                                
                                # Match sound
                                if sound_enabled:
                                    match_sound = generate_tone(660, 0.3)  # E5 note
                                    if match_sound is not None:
                                        audio_data = create_audio_data(match_sound)
                                        if audio_data:
                                            with sound_container:
                                                st.markdown(f'<audio autoplay><source src="{audio_data}" type="audio/wav"></source></audio>', 
                                                          unsafe_allow_html=True)
                                
                                # Check for game over
                                if game["score"] == game["num_pairs"]:
                                    game["game_over"] = True
                                    game["game_just_completed"] = True
                                    # Victory sound
                                    if sound_enabled:
                                        victory_sound = generate_tone(880, 0.5)  # A5 note
                                        if victory_sound is not None:
                                            audio_data = create_audio_data(victory_sound)
                                            if audio_data:
                                                with sound_container:
                                                    st.markdown(f'<audio autoplay><source src="{audio_data}" type="audio/wav"></audio>', 
                                                              unsafe_allow_html=True)
                            else:
                                # No match - start waiting
                                game["waiting"] = True
                                game["wait_start"] = time.time()
                                game["last_match"] = False
                                # Miss sound
                                if sound_enabled:
                                    miss_sound = generate_tone(220, 0.2)  # A3 note
                                    if miss_sound is not None:
                                        audio_data = create_audio_data(miss_sound)
                                        if audio_data:
                                            with sound_container:
                                                st.markdown(f'<audio autoplay><source src="{audio_data}" type="audio/wav"></audio>', 
                                                          unsafe_allow_html=True)
                        
                        should_rerun = True
                else:
                    # Waiting state - show disabled card with consistent styling
                    st.markdown(f'<div class="card-button card-unflipped">❓</div>', 
                              unsafe_allow_html=True)
                    st.button("", key=f"card_{i}", disabled=True, 
                             help="Wait for cards to flip back")

# Status messages and game completion
with status_container:
    if game.get("game_over", False):
        if game.get("game_just_completed", False):
            st.balloons()
            game["game_just_completed"] = False  # Reset flag
        
        winner_text = ""
        if mode == "Solo":
            winner_text = f"🎉 Congratulations **{player_names[0] if player_names[0] else 'Player'}**, you finished the game in {game['moves']} moves!"
        else:
            max_score = max(game["player_scores"])
            winners = [game["player_names"][i] for i, sc in enumerate(game["player_scores"]) if sc == max_score]
            if len(winners) == 1:
                winner_text = f"🎉 Congratulations **{winners[0]}**, you won with {max_score} pairs!"
            else:
                winner_text = f"🎉 It's a tie between {', '.join(winners)} with {max_score} pairs!"
        
        st.success(winner_text)
        
        # Calculate efficiency
        optimal_moves = game["num_pairs"]
        efficiency = (optimal_moves / game["moves"]) * 100 if game["moves"] > 0 else 0
        efficiency_text = "Perfect!" if efficiency == 100 else f"{efficiency:.1f}%"
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Moves", game["moves"])
        with col2:
            st.metric("Efficiency", efficiency_text)
        with col3:
            if game.get("start_time"):
                duration = time.time() - game["start_time"]
                st.metric("Time", f"{duration:.1f}s")
        
        # Auto-submit score for solo mode
        if mode == "Solo" and not game.get("score_submitted", False):
            name = player_names[0].strip()
            if name == "":
                st.warning("Please enter your name in the sidebar to submit your score.")
            else:
                leaderboard = load_leaderboard()
                now_str = malaysia_time().strftime("%Y-%m-%d %H:%M:%S")
                new_row = pd.DataFrame([{
                    "Name": name,
                    "Difficulty": difficulty,
                    "Moves": game["moves"],
                    "Date": now_str,
                }])
                leaderboard = pd.concat([leaderboard, new_row], ignore_index=True)
                save_leaderboard(leaderboard)
                st.success(f"Score submitted for **{name}**!")
                game["score_submitted"] = True
    
    elif game["waiting"]:
        st.info("🤔 Cards will flip back in a moment...")
    elif game["last_match"]:
        st.success("🎯 Great match! Keep going!")

if mode == "Solo" and game.get("score_submitted", False) and not game.get("game_just_completed", False):
    st.info("Score submitted! Start a new game to submit another score.")

# New game button
if st.button("🔄 New Game"):
    st.session_state.game = init_game(rows, cols, player_names)
    should_rerun = True

# Single strategic rerun
if should_rerun:
    st.rerun()

# Leaderboard display (cached)
st.markdown("---")
st.header("🏅 Leaderboard")

leaderboard = load_leaderboard()
filtered_board = leaderboard[leaderboard["Difficulty"] == difficulty]
if filtered_board.empty:
    st.info("No leaderboard entries yet. Be the first!")
else:
    sorted_leaderboard = filtered_board.sort_values(by=["Moves", "Date"]).head(10).reset_index(drop=True)
    sorted_leaderboard.index += 1  # Start ranking from 1
    st.dataframe(sorted_leaderboard, use_container_width=True)

st.markdown("---")
st.caption("© 2025 Memory Puzzle Game | Enhanced with ❤️")
