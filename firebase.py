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
            # Check if secrets are configured
            if "firebase_key" not in st.secrets:
                st.error("Firebase key not found in Streamlit secrets. Please add your Firebase credentials to Streamlit secrets.")
                raise Exception("Firebase key not found in Streamlit secrets")
            
            if "FIREBASE_DATABASE_URL" not in st.secrets:
                st.error("Firebase database URL not found in Streamlit secrets. Please add your Firebase database URL to Streamlit secrets.")
                raise Exception("Firebase database URL not found in Streamlit secrets")

            # Get Firebase credentials from Streamlit secrets
            try:
                firebase_key = st.secrets["firebase_key"]
                cred_dict = json.loads(firebase_key)
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError:
                st.error("Invalid Firebase key format in Streamlit secrets. Please check your Firebase credentials.")
                raise Exception("Invalid Firebase key format")
            except Exception as e:
                st.error(f"Error processing Firebase credentials: {str(e)}")
                raise Exception(f"Error processing Firebase credentials: {str(e)}")
            
            # Get database URL from Streamlit secrets
            database_url = st.secrets["FIREBASE_DATABASE_URL"]
            
            # Initialize Firebase
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
            st.success("Firebase initialized successfully!")
            
        except Exception as e:
            st.error(f"Failed to initialize Firebase: {str(e)}")
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
