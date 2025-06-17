import firebase_admin
from firebase_admin import credentials, db
import streamlit as st
import json
import os

def init_firebase() -> None:
    """
    Initialize Firebase connection if not already initialized.
    Uses Streamlit secrets for authentication.
    """
    if not firebase_admin._apps:
        try:
            # Get Firebase credentials from Streamlit secrets
            firebase_key = st.secrets["firebase_key"]
            cred_dict = json.loads(firebase_key)
            cred = credentials.Certificate(cred_dict)
            
            # Get database URL from Streamlit secrets
            database_url = st.secrets["FIREBASE_DATABASE_URL"]
            
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
        except Exception as e:
            st.error(f"Failed to initialize Firebase. Please check your Streamlit secrets configuration.")
            raise Exception(f"Failed to initialize Firebase: {str(e)}")

def get_room_ref(room_id: str) -> db.Reference:
    """
    Get a reference to a specific game room in Firebase.
    
    Args:
        room_id (str): The ID of the game room
        
    Returns:
        db.Reference: Firebase database reference to the room
    """
    init_firebase()
    return db.reference(f'/rooms/{room_id}')
