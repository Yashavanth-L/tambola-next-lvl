# Tambola Next Level

A multiplayer Tambola (Housie) game built with Streamlit and Firebase.

## Features
- Multiplayer support
- Real-time game updates
- QR code generation for easy joining
- Interactive ticket marking
- Achievement tracking
- Winner display

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Firebase:
   - Create a Firebase project
   - Enable Realtime Database
   - Download your Firebase service account key and save it as `firebase_key.json`

## Deployment

### Deploying to Streamlit Cloud

1. Create a GitHub repository and push your code
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with your GitHub account
4. Click "New app"
5. Select your repository, branch, and main file (app.py)
6. Add your Firebase credentials as secrets:
   - Go to your app settings
   - Add a new secret with key `firebase_key` and value as the contents of your `firebase_key.json`

### Environment Variables
Make sure to set these in your deployment environment:
- `FIREBASE_DATABASE_URL`: Your Firebase Realtime Database URL

## Local Development

Run the app locally:
```bash
streamlit run app.py
```

## Security Notes
- Never commit `firebase_key.json` to version control
- Use environment variables for sensitive data
- Keep your Firebase rules secure 