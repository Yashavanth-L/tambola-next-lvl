import streamlit as st
st.set_page_config(initial_sidebar_state="collapsed")
import firebase_admin
from firebase_admin import credentials, db
from ticket_generator import generate_ticket
import random

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://tambola-game-f9536-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })

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
    st.stop()

# Get room data
room_ref = db.reference(f"rooms/{room_id}")
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

# --- Tambola Achievements Logic ---
def check_achievements():
    achievements = room_data.get("achievements", {})
    housie_winners = achievements.get("fullhousie_winners", [])
    total_players = len(players)
    updated = False
    
    # 1. First 5
    if "first5" not in achievements:
        marked_count = sum(sum(1 for c in range(9) if ticket[r][c] != 0 and marked[r][c]) for r in range(3))
        if marked_count >= 5:
            achievements["first5"] = player_name
            updated = True
    
    # 2. Corner Fours
    if "corners" not in achievements:
        corners = [(0,0), (0,8), (2,0), (2,8)]
        corner_nums = [ticket[r][c] for r, c in corners]
        if all(ticket[r][c] != 0 and marked[r][c] for r, c in corners):
            achievements["corners"] = player_name
            updated = True
    
    # 3. First Line
    if "firstline" not in achievements:
        if sum(1 for c in range(9) if ticket[0][c] != 0 and marked[0][c]) == 5:
            achievements["firstline"] = player_name
            updated = True
    
    # 4. Second Line
    if "secondline" not in achievements:
        if sum(1 for c in range(9) if ticket[1][c] != 0 and marked[1][c]) == 5:
            achievements["secondline"] = player_name
            updated = True
    
    # 5. Last Line
    if "lastline" not in achievements:
        if sum(1 for c in range(9) if ticket[2][c] != 0 and marked[2][c]) == 5:
            achievements["lastline"] = player_name
            updated = True
    
    # 6. Full Housie (Multiple Winners)
    if player_name not in housie_winners:  # Check if this player hasn't won yet
        if sum(sum(1 for c in range(9) if ticket[r][c] != 0 and marked[r][c]) for r in range(3)) == 15:
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
achievement_labels = [
    ("first5", "First 5 🎯"),
    ("corners", "Corner Fours 🎲"),
    ("firstline", "First Line 1️⃣"),
    ("secondline", "Second Line 2️⃣"),
    ("lastline", "Last Line 3️⃣")
]

st.markdown("## 🏆 Achievements")
# Display regular achievements
for key, label in achievement_labels:
    winner = achievements.get(key)
    if winner:
        st.success(f"{label}: Winner is {winner} 🌟")
    else:
        st.info(f"{label}: Not claimed yet")

# Display Full Housie winners
housie_winners = achievements.get("fullhousie_winners", [])
if housie_winners:
    st.markdown("### 🏆 Full Housie Winners")
    for idx, winner in enumerate(housie_winners, 1):
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(idx, "th")
        st.success(f"{idx}{suffix} Place: {winner} 🌟")
else:
    st.info("Full Housie: Not claimed yet")

# --- Tambola Ticket UI ---
st.title(f"Welcome, {player_name}!")
st.subheader(f"Room ID: {room_id}")
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
if called_numbers:
    st.markdown("### 📢 Called Numbers:")
    st.markdown(f"**Last called: {called_numbers[-1]}**")
    st.markdown(f"All numbers: {', '.join(map(str, called_numbers))}")

# Show number generator for host (only if game is not complete)
if player_name == room_data.get("host") and not achievements.get("game_complete"):
    st.markdown("---")
    if st.button("🔢 Generate Next Number"):
        all_numbers = list(range(1, 91))
        remaining = list(set(all_numbers) - set(called_numbers))
        
        if not remaining:
            st.success("No more numbers to call!")
        else:
            next_num = random.choice(remaining)
            called_numbers.append(next_num)
            room_ref.update({"called_numbers": called_numbers})
            st.success(f"Next number is: {next_num}")

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