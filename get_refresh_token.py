"""
get_refresh_token.py — One-time helper to get GOOGLE_REFRESH_TOKEN for your YouTube channel.
"""
import urllib.parse, urllib.request, json

CLIENT_ID = input("Paste GOOGLE_CLIENT_ID: ").strip()
CLIENT_SECRET = input("Paste GOOGLE_CLIENT_SECRET: ").strip()
REDIRECT = "https://developers.google.com/oauthplayground"

auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": CLIENT_ID, "redirect_uri": REDIRECT, "response_type": "code",
    "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.force-ssl",
    "access_type": "offline", "prompt": "consent",
})
print("\n1) Open this URL and select the EXACT target YouTube channel:\n")
print(auth_url)
code = input("\n2) Paste the 'code=...' value here: ").strip()

req = urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=urllib.parse.urlencode({
        "code": code, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code",
    }).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
with urllib.request.urlopen(req) as r:
    tok = json.loads(r.read().decode())
print("\nSUCCESS! Save this as GitHub Secret GOOGLE_REFRESH_TOKEN:\n")
print(tok.get("refresh_token"))
