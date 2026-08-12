import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

UPSTREAM_URL = os.getenv("UPSTREAM_URL")
UPSTREAM_BEARER_TOKEN = os.getenv("UPSTREAM_BEARER_TOKEN")

DEVELOPER = "MOHD ZUBAIR"
TELEGRAM = "https://t.me/ZB15y"
WHATSAPP = "https://wa.me/+584167861851"

PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def info():
    return {
        "developer": DEVELOPER,
        "telegram": TELEGRAM,
        "whatsapp": WHATSAPP
    }


@app.get("/")
def home():
    return jsonify({
        "api": "PAN Info API",
        "status": "online",
        **info()
    })


@app.get("/pan-info")
def pan_info():
    pan = request.args.get("pan", "").strip().upper()

    if not PAN_PATTERN.fullmatch(pan):
        return jsonify({
            "error": "Invalid PAN format",
            **info()
        }), 400

    if not UPSTREAM_URL or not UPSTREAM_BEARER_TOKEN:
        return jsonify({
            "error": "Upstream configuration missing",
            **info()
        }), 500

    try:
        response = requests.get(
            UPSTREAM_URL,
            params={"pan": pan},
            headers={
                "Authorization": f"Bearer {UPSTREAM_BEARER_TOKEN}",
                "Accept": "application/json"
            },
            timeout=15
        )

        try:
            result = response.json()
        except ValueError:
            result = {
                "error": "Upstream returned non-JSON response",
                "status_code": response.status_code
            }

        if isinstance(result, dict):
            result.update(info())
        else:
            result = {
                "data": result,
                **info()
            }

        return jsonify(result), response.status_code

    except requests.Timeout:
        return jsonify({
            "error": "Upstream timeout",
            **info()
        }), 504

    except requests.RequestException:
        return jsonify({
            "error": "Could not connect to upstream service",
            **info()
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
