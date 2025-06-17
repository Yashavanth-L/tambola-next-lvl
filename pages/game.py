import streamlit as st
st.set_page_config(initial_sidebar_state="collapsed")
import firebase_admin
from firebase_admin import db
from firebase import init_firebase, get_room_ref
from ticket_generator import generate_ticket
import random
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import numpy as np
import time

# Initialize Firebase
init_firebase()

# Get URL parameters
room_id = st.query_params.get("room_id", None)
player_name = st.query_params.get("player_name", None)

# Defensive: strip and uppercase room_id
if room_id:
    room_id = room_id.strip().upper()
if player_name:
    player_name = player_name.strip()

# Validate params and room_id format
if not room_id or len(room_id) != 6 or not player_name:
    st.error("Invalid or missing game link. Please use the join link provided by the host.")
    st.markdown("""
    ### How to join the game:
    1. Ask the host to create a game room
    2. Use the join link or QR code provided by the host
    3. Make sure you're using the correct link for your player name
    """)
    st.stop()

# Get room data
room_ref = get_room_ref(room_id)
room_data = room_ref.get()

if not room_data:
    st.error("Room not found.")
    st.stop()

# Get player data
players = room_data.get("players", {})
player_data = players.get(player_name)

if not player_data:
    st.error("Player not found in this room.")
    st.stop()

# Generate ticket if player doesn't have one
if not player_data.get("ticket"):
    ticket = generate_ticket()
    players[player_name]["ticket"] = ticket
    players[player_name]["marked"] = [[False for _ in range(9)] for _ in range(3)]
    players[player_name]["joined"] = True
    room_ref.update({"players": players})
else:
    ticket = player_data["ticket"]
    if "marked" not in player_data:
        player_data["marked"] = [[False for _ in range(9)] for _ in range(3)]
    if not player_data.get("joined"):
        players[player_name]["joined"] = True
    room_ref.update({"players": players})

# Get marked positions from Firebase
marked = player_data.get("marked", [[False for _ in range(9)] for _ in range(3)])

# Add auto-refresh functionality
def auto_refresh():
    # Get latest room data
    latest_room_data = room_ref.get()
    if latest_room_data:
        # Get latest called numbers
        latest_called_numbers = latest_room_data.get("called_numbers", [])
        current_called_numbers = room_data.get("called_numbers", [])
        
        # If new numbers were called, update the UI
        if len(latest_called_numbers) > len(current_called_numbers):
            st.rerun()

# Set up auto-refresh with a shorter interval (2 seconds)
st_autorefresh(interval=2000, key="game_refresh")

# --- Tambola Ticket UI ---
st.title(f"Welcome, {player_name}!")
st.subheader(f"Room ID: {room_id}")

# Add Generate Next Number button at the top (only for host)
if player_name == room_data.get("host"):
    if st.button("🎲 Generate Next Number"):
        # Get current called numbers
        called_numbers = room_data.get("called_numbers", [])
        
        # Generate a new number that hasn't been called
        available_numbers = [n for n in range(1, 91) if n not in called_numbers]
        if available_numbers:
            new_number = random.choice(available_numbers)
            called_numbers.append(new_number)
            room_ref.update({"called_numbers": called_numbers})
            st.rerun()

st.markdown("### 🎫 Your Tambola Ticket:")

# Get called numbers
called_numbers = room_data.get("called_numbers", [])

# Render the ticket as a single HTML table for proper alignment
cell_style = "height:40px;width:40px;text-align:center;font-size:20px;border:1.5px solid #222;"
alt_bg = "background-color:#ffe5cc;"
table_html = '<div style="display:inline-block;border:5px solid black;padding:8px;margin-bottom:10px;">'
table_html += '<div style="text-align:center;font-weight:bold;font-size:18px;margin-bottom:10px;">Tambola ticket</div>'
table_html += '<table style="border-collapse:collapse;margin:auto;">'
for row_idx, row in enumerate(ticket):
    table_html += '<tr>'
    for col_idx, val in enumerate(row):
        style = cell_style
        if (row_idx + col_idx) % 2 == 0:
            style += alt_bg
        if val == 0:
            table_html += f'<td style="{style}"></td>'
        else:
            if val in called_numbers:
                if marked[row_idx][col_idx]:
                    # Number is called and marked
                    table_html += f'<td style="{style};background:#f9d6d5;border:2px solid #d9534f;"><s>{val}</s></td>'
                else:
                    # Number is called but not marked
                    table_html += f'<td style="{style};background:#dff0d8;border:2px solid #5cb85c;">{val}</td>'
            else:
                # Number is not called yet
                table_html += f'<td style="{style}">{val}</td>'
    table_html += '</tr>'
table_html += '</table></div>'
st.markdown(table_html, unsafe_allow_html=True)

# Show called numbers
st.markdown("### 📢 Called Numbers:")
if called_numbers:
    st.write(", ".join(map(str, called_numbers)))
else:
    st.write("No numbers called yet")

# --- Tambola Achievements Logic ---
def check_achievements():
    achievements = room_data.get("achievements", {})
    housie_winners = achievements.get("fullhousie_winners", [])
    total_players = len(players)
    updated = False
    
    # Helper function to count marked numbers in a row
    def count_marked_in_row(row_idx):
        return sum(1 for c in range(9) if ticket[row_idx][c] != 0 and marked[row_idx][c])
    
    # Helper function to count total marked numbers
    def count_total_marked():
        return sum(count_marked_in_row(r) for r in range(3))
    
    # 1. First 5
    if "first5" not in achievements:
        if count_total_marked() >= 5:
            achievements["first5"] = player_name
            updated = True
            st.balloons()
            st.success(f"🎯 Congratulations! {player_name} has achieved First 5! 🎉")
    
    # 2. Corner Fours
    if "corners" not in achievements:
        corners = [(0,0), (0,8), (2,0), (2,8)]
        if all(ticket[r][c] != 0 and marked[r][c] for r, c in corners):
            achievements["corners"] = player_name
            updated = True
            st.balloons()
            st.success(f"🎲 Congratulations! {player_name} has achieved Corner Fours! 🎉")
    
    # 3. First Line
    if "firstline" not in achievements:
        if count_marked_in_row(0) == 5:
            achievements["firstline"] = player_name
            updated = True
            st.balloons()
            st.success(f"1️⃣ Congratulations! {player_name} has completed the First Line! 🎉")
    
    # 4. Second Line
    if "secondline" not in achievements:
        if count_marked_in_row(1) == 5:
            achievements["secondline"] = player_name
            updated = True
            st.balloons()
            st.success(f"2️⃣ Congratulations! {player_name} has completed the Second Line! 🎉")
    
    # 5. Last Line
    if "lastline" not in achievements:
        if count_marked_in_row(2) == 5:
            achievements["lastline"] = player_name
            updated = True
            st.balloons()
            st.success(f"3️⃣ Congratulations! {player_name} has completed the Last Line! 🎉")
    
    # 6. Full Housie (Multiple Winners)
    if player_name not in housie_winners:  # Check if this player hasn't won yet
        if count_total_marked() == 15:  # All numbers are marked
            housie_winners.append(player_name)
            achievements["fullhousie_winners"] = housie_winners
            updated = True
            
            # Show winner popup
            position = len(housie_winners)
            if position == 1:
                st.balloons()
                st.success(f"🏆 Congratulations! {player_name} has won FIRST place in Full Housie! 🎉")
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(position, "th")
                st.success(f"🏆 {player_name} has won {position}{suffix} place in Full Housie! 🎉")
            
            # Check if game should end (n-1 players have won)
            if len(housie_winners) >= total_players - 1:
                achievements["game_complete"] = True
                st.warning("Game Over! All but one player have completed Full Housie!")
    
    if updated:
        room_ref.update({"achievements": achievements})
    return achievements

# --- Display Achievements ---
achievements = check_achievements()

# Create a container for achievements with custom styling
st.markdown("""
    <style>
    .achievement-container {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .achievement-title {
        color: #1f77b4;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .achievement-item {
        background-color: white;
        border-radius: 8px;
        padding: 10px 15px;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .achievement-winner {
        color: #28a745;
        font-weight: bold;
    }
    .achievement-pending {
        color: #6c757d;
    }
    .housie-winners {
        background-color: #fff3cd;
        border-radius: 8px;
        padding: 15px;
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# Main achievements section
st.markdown('<div class="achievement-container">', unsafe_allow_html=True)
st.markdown('<div class="achievement-title">🏆 Game Achievements</div>', unsafe_allow_html=True)

# Regular achievements with improved styling
achievement_labels = [
    ("first5", "First 5 🎯", "Be the first to mark 5 numbers"),
    ("corners", "Corner Fours 🎲", "Mark all four corner numbers"),
    ("firstline", "First Line 1️⃣", "Complete the first line"),
    ("secondline", "Second Line 2️⃣", "Complete the second line"),
    ("lastline", "Last Line 3️⃣", "Complete the last line")
]

for key, label, description in achievement_labels:
    winner = achievements.get(key)
    if winner:
        st.markdown(f"""
            <div class="achievement-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{label}</strong><br>
                        <small>{description}</small>
                    </div>
                    <div class="achievement-winner">Winner: {winner} 🌟</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="achievement-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{label}</strong><br>
                        <small>{description}</small>
                    </div>
                    <div class="achievement-pending">Not claimed yet</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# Full Housie winners section
st.markdown('<div class="housie-winners">', unsafe_allow_html=True)
st.markdown('<div class="achievement-title">🏆 Full Housie Winners</div>', unsafe_allow_html=True)

housie_winners = achievements.get("fullhousie_winners", [])
if housie_winners:
    for idx, winner in enumerate(housie_winners, 1):
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(idx, "th")
        st.markdown(f"""
            <div class="achievement-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{idx}{suffix} Place</strong><br>
                        <small>Complete all numbers on the ticket</small>
                    </div>
                    <div class="achievement-winner">{winner} 🌟</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class="achievement-item">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>Full Housie</strong><br>
                    <small>Complete all numbers on the ticket</small>
                </div>
                <div class="achievement-pending">Not claimed yet</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)

# Auto-mark called numbers
if called_numbers:
    for row_idx in range(3):
        for col_idx in range(9):
            val = ticket[row_idx][col_idx]
            if val in called_numbers and not marked[row_idx][col_idx]:
                marked[row_idx][col_idx] = True
                players[player_name]["marked"] = marked
                room_ref.update({"players": players})
                check_achievements() 