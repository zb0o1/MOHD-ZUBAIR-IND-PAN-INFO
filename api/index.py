import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

UPSTREAM_URL = os.getenv("UPSTREAM_URL", "").strip()
UPSTREAM_BEARER_TOKEN = os.getenv("UPSTREAM_BEARER_TOKEN", "").strip()

DEVELOPER = "MOHD ZUBAIR"
TELEGRAM = "https://t.me/ZB15y"
WHATSAPP = "https://wa.me/+584167861851"

PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def footer():
    return {
        "developer": DEVELOPER,
        "telegram": TELEGRAM,
        "whatsapp": WHATSAPP
    }


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api": "MOHD ZUBAIR PAN API",
        "status": "online",
        "usage": "/api/pan?info=ABCDE1234F",
        **footer()
    })


@app.route("/api/pan", methods=["GET"])
def pan():

    value = request.args.get("info", "").strip().upper()

    if not PAN_RE.fullmatch(value):
        return jsonify({
            "error": "Valid 10-character PAN format required",
            "usage": "/api/pan?info=ABCDE1234F",
            **footer()
        }), 400

    if not UPSTREAM_URL:
        return jsonify({
            "error": "UPSTREAM_URL is not configured",
            **footer()
        }), 500

    if not UPSTREAM_BEARER_TOKEN:
        return jsonify({
            "error": "UPSTREAM_BEARER_TOKEN is not configured",
            **footer()
        }), 500

    headers = {
        "Authorization": f"Bearer {UPSTREAM_BEARER_TOKEN}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            UPSTREAM_URL,
            params={"pan": value},
            headers=headers,
            timeout=15
        )

        try:
            result = response.json()
        except ValueError:
            result = {
                "upstream_status": response.status_code,
                "upstream_response": response.text[:2000]
            }

        if isinstance(result, dict):
            result.update(footer())
        else:
            result = {
                "data": result,
                **footer()
            }

        return jsonify(result), response.status_code

    except requests.Timeout:
        return jsonify({
            "error": "Upstream request timed out",
            **footer()
        }), 504

    except requests.RequestException as exc:
        return jsonify({
            "error": "Upstream request failed",
            "details": str(exc),
            **footer()
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
