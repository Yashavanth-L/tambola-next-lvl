import streamlit as st
st.set_page_config(initial_sidebar_state="collapsed", layout="wide")
import firebase_admin
from firebase_admin import db
from firebase import init_firebase, get_room_ref
from ticket_generator import generate_ticket
import random
import pandas as pd
import numpy as np
import time

# Try to import autorefresh, but don't fail if it's not available
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False
    st.warning("Auto-refresh is not available. The page will need to be manually refreshed to see updates.")

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

# Set up auto-refresh with a shorter interval (2 seconds) if available
if AUTOREFRESH_AVAILABLE:
    st_autorefresh(interval=2000, key="game_refresh")
else:
    # Add a manual refresh button
    if st.button("🔄 Refresh Game"):
        st.rerun()

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

# Create two columns for the layout
col1, col2 = st.columns([0.6, 0.4])

with col1:
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

with col2:
    st.markdown("### 🏆 Game Achievements")
    
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
    
    # 2. First Line
    if "firstline" not in achievements:
        if count_marked_in_row(0) == 5:
            achievements["firstline"] = player_name
            updated = True
            st.balloons()
            st.success(f"1️⃣ Congratulations! {player_name} has completed the First Line! 🎉")
    
    # 3. Second Line
    if "secondline" not in achievements:
        if count_marked_in_row(1) == 5:
            achievements["secondline"] = player_name
            updated = True
            st.balloons()
            st.success(f"2️⃣ Congratulations! {player_name} has completed the Second Line! 🎉")
    
    # 4. Last Line
    if "lastline" not in achievements:
        if count_marked_in_row(2) == 5:
            achievements["lastline"] = player_name
            updated = True
            st.balloons()
            st.success(f"3️⃣ Congratulations! {player_name} has completed the Last Line! 🎉")
    
    # 5. Full Housie (Multiple Winners)
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

# Display current achievements in the right column
with col2:
    achievement_list = [
        ("🎯 First 5", "first5"),
        ("1️⃣ First Line", "firstline"),
        ("2️⃣ Second Line", "secondline"),
        ("3️⃣ Last Line", "lastline")
    ]
    
    for label, key in achievement_list:
        winner = achievements.get(key)
        if winner:
            st.success(f"{label}: {winner}")
        else:
            st.info(f"{label}: Not achieved yet")
    
    # Display Full Housie winners
    st.markdown("### 🏆 Full Housie Winners")
    housie_winners = achievements.get("fullhousie_winners", [])
    if housie_winners:
        for idx, winner in enumerate(housie_winners, 1):
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(idx, "th")
            st.success(f"{idx}{suffix} Place: {winner}")
    else:
        st.info("No winners yet")

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