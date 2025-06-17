# Tambola Next Level

A multiplayer Tambola (Housie) game built with Streamlit and Firebase.

## Features

- Real-time multiplayer gameplay
- Automatic ticket generation
- Number calling system
- Win pattern validation
- Player statistics

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tambola-next-lvl.git
cd tambola-next-lvl
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Firebase:
- Create a Firebase project
- Enable Realtime Database
- Create a service account and download the credentials

4. Set up Streamlit secrets:
- Create a `.streamlit/secrets.toml` file
- Add your Firebase credentials:
```toml
firebase_key = """
{
    "type": "service_account",
    "project_id": "YOUR_PROJECT_ID",
    "private_key_id": "YOUR_PRIVATE_KEY_ID",
    "private_key": "YOUR_PRIVATE_KEY",
    "client_email": "YOUR_CLIENT_EMAIL",
    "client_id": "YOUR_CLIENT_ID",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "YOUR_CERT_URL"
}
"""

FIREBASE_DATABASE_URL = "YOUR_FIREBASE_DATABASE_URL"
```

5. Run the application:
```bash
streamlit run app.py
```

## Deployment

1. Create a Streamlit account at https://streamlit.io
2. Install Streamlit CLI:
```bash
pip install streamlit
```
3. Deploy to Streamlit:
```bash
streamlit deploy
```

## Security Notes

- Keep your Streamlit secrets secure
- Never commit `.streamlit/secrets.toml` to version control
- Keep your Firebase rules secure

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 