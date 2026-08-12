import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==================== CONFIG ====================

BASE_URL = os.getenv("UPSTREAM_URL", "").strip()
BEARER_TOKEN = os.getenv("UPSTREAM_BEARER_TOKEN", "").strip()

DEVELOPER = "MOHD ZUBAIR"
TELEGRAM = "https://t.me/ZB15y"
WHATSAPP = "https://wa.me/+584167861851"

PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def developer_info():
    return {
        "developer": DEVELOPER,
        "telegram": TELEGRAM,
        "whatsapp": WHATSAPP
    }


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api": "PAN to Info API",
        "status": "online",
        "usage": "/pan-info?pan=JCZPS4827P",
        "example": "/pan-info?pan=JCZPS4827P",
        **developer_info()
    })


@app.route("/pan-info", methods=["GET"])
def pan_info():

    pan = request.args.get("pan", "").strip().upper()

    if not PAN_PATTERN.fullmatch(pan):
        return jsonify({
            "error": "Valid 10-digit PAN required",
            "example": "/pan-info?pan=JCZPS4827P",
            **developer_info()
        }), 400

    if not BASE_URL:
        return jsonify({
            "error": "UPSTREAM_URL is not configured",
            **developer_info()
        }), 500

    if not BEARER_TOKEN:
        return jsonify({
            "error": "UPSTREAM_BEARER_TOKEN is not configured",
            **developer_info()
        }), 500

    # Use only headers documented/authorized by the upstream API.
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            BASE_URL,
            params={"pan": pan},
            headers=headers,
            timeout=15
        )

        try:
            data = response.json()
        except ValueError:
            data = {
                "error": "Upstream returned a non-JSON response",
                "status_code": response.status_code,
                "raw_response": response.text[:1000]
            }

        if isinstance(data, dict):
            data.update(developer_info())
        else:
            data = {
                "data": data,
                **developer_info()
            }

        return jsonify(data), response.status_code

    except requests.Timeout:
        return jsonify({
            "error": "Upstream request timed out",
            **developer_info()
        }), 504

    except requests.RequestException as exc:
        return jsonify({
            "error": "Upstream request failed",
            "details": str(exc),
            **developer_info()
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
