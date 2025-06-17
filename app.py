import streamlit as st
import uuid
import qrcode
from io import BytesIO
from firebase import get_room_ref

# Configure page
st.set_page_config(
    page_title="Tambola Time",
    page_icon="🎲",
    layout="centered"
)

def create_game_room(player_names):
    """Create a new game room and return room details"""
    room_id = str(uuid.uuid4())[:6].upper()
    ref = get_room_ref(room_id)
    
    ref.set({
        "numbers": [],
        "players": {name: {"joined": False} for name in player_names},
        "host": player_names[0],
        "expected_players": len(player_names),
        "called_numbers": []
    })
    
    return room_id

def generate_join_links(room_id, player_names):
    """Generate join links and QR codes for players"""
    # Get the current URL from Streamlit
    base_url = st.experimental_get_query_params().get("base_url", [st.get_option("server.address")])[0]
    if not base_url.startswith("http"):
        base_url = f"https://{base_url}"
    
    join_details = []
    
    for name in player_names:
        join_link = f"{base_url}/game?room_id={room_id}&player_name={name}"
        qr = qrcode.make(join_link)
        buf = BytesIO()
        qr.save(buf)
        join_details.append({
            "name": name,
            "link": join_link,
            "qr_code": buf.getvalue()
        })
    
    return join_details

# Main UI
st.title("🎉 Tambola Multiplayer Setup")
st.markdown("Create a room, set player names, and generate QR codes to join!")

# Get number of players
num_players = st.number_input(
    "How many players are joining?",
    min_value=2,
    max_value=10,
    step=1
)

# Get player names
player_names = []
for i in range(num_players):
    name = st.text_input(f"Enter name for Player {i+1}", key=f"player_{i}")
    player_names.append(name)

# Create room button
if st.button("Create Game Room") and all(player_names):
    room_id = create_game_room(player_names)
    st.success(f"✅ Room `{room_id}` created!")

    # Generate and display join links
    join_details = generate_join_links(room_id, player_names)
    
    for details in join_details:
        st.markdown(f"**{details['name']}** → [Join Link]({details['link']})")
        st.image(details['qr_code'], caption=f"Scan to Join as {details['name']}", width=200)

    st.session_state.room_id = room_id
