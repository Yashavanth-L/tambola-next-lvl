import firebase_admin
from firebase_admin import credentials, db
from typing import Optional
import os
import json

def init_firebase() -> None:
    """
    Initialize Firebase connection if not already initialized.
    Uses environment variables or firebase_key.json file for authentication.
    """
    if not firebase_admin._apps:
        try:
            # Try to get Firebase credentials from environment variable first
            firebase_key = os.getenv('FIREBASE_KEY')
            if firebase_key:
                cred_dict = json.loads(firebase_key)
                cred = credentials.Certificate(cred_dict)
            else:
                # Fallback to firebase_key.json file
                cred = credentials.Certificate("firebase_key.json")

            # Get database URL from environment variable or use default
            database_url = os.getenv('FIREBASE_DATABASE_URL', 
                'https://tambola-game-f9536-default-rtdb.asia-southeast1.firebasedatabase.app/')

            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
        except Exception as e:
            raise Exception(f"Failed to initialize Firebase: {str(e)}")

def get_room_ref(room_id: str) -> Optional[db.Reference]:
    """
    Get a reference to a specific game room in Firebase.
    
    Args:
        room_id (str): The unique identifier for the game room
        
    Returns:
        db.Reference: Firebase database reference to the room
    """
    init_firebase()
    return db.reference(f"rooms/{room_id}")
