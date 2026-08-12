import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ============================================================
# CONFIG — SET THESE IN VERCEL ENVIRONMENT VARIABLES
# ============================================================

BASE_URL = os.environ.get(
    "UPSTREAM_URL",
    "https://turtlemintloans.com/api/minterprise/v1/products/personal-loan/leads/existing-lead-by-pan"
)

BEARER_TOKEN = os.environ.get("UPSTREAM_BEARER_TOKEN", "")

# Optional upstream values — only use values you are authorized
# to use with the upstream service.
X_BROKER = os.environ.get("UPSTREAM_X_BROKER", "turtlemint")
X_PROVIDER = os.environ.get("UPSTREAM_X_PROVIDER", "signzy")
X_TENANT = os.environ.get("UPSTREAM_X_TENANT", "turtlemint")
X_PARTNER_ID = os.environ.get("UPSTREAM_X_PARTNER_ID", "undefined")

# ============================================================
# YOUR API INFORMATION
# ============================================================

DEVELOPER = "MOHD ZUBAIR"
TELEGRAM = "https://t.me/ZB15y"
WHATSAPP = "https://wa.me/+584167861851"

# Standard PAN format
PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def add_developer_info(data):
    """
    Adds developer information after upstream response.
    """

    if isinstance(data, dict):
        data["developer"] = DEVELOPER
        data["telegram"] = TELEGRAM
        data["whatsapp"] = WHATSAPP
        return data

    return {
        "data": data,
        "developer": DEVELOPER,
        "telegram": TELEGRAM,
        "whatsapp": WHATSAPP
    }


def upstream_headers():
    return {
        "x-broker": X_BROKER,
        "authorization": f"Bearer {BEARER_TOKEN}",
        "x-provider": X_PROVIDER,
        "x-partner-id": X_PARTNER_ID,
        "x-tenant": X_TENANT,
        "accept": "application/json",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0",
    }


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api": "PAN to Info API",
        "status": "online",
        "developer": DEVELOPER,
        "telegram": TELEGRAM,
        "whatsapp": WHATSAPP,
        "usage": "/pan-info?pan=ABCDE1234F"
    })


@app.route("/pan-info", methods=["GET"])
def pan_info():

    pan = request.args.get("pan", "").strip().upper()

    # Validate PAN properly
    if not PAN_PATTERN.fullmatch(pan):
        return jsonify({
            "error": "Valid 10-digit PAN required",
            "example": "/pan-info?pan=ABCDE1234F",
            "developer": DEVELOPER,
            "telegram": TELEGRAM,
            "whatsapp": WHATSAPP
        }), 400

    # Make sure secret exists
    if not BEARER_TOKEN:
        return jsonify({
            "error": "Upstream API configuration is missing",
            "developer": DEVELOPER,
            "telegram": TELEGRAM,
            "whatsapp": WHATSAPP
        }), 500

    try:
        response = requests.get(
            BASE_URL,
            params={"pan": pan},
            headers=upstream_headers(),
            timeout=15
        )

        # JSON response
        try:
            data = response.json()

        except ValueError:
            data = {
                "raw_response": response.text[:1000]
            }

        # Add your information to successful response
        data = add_developer_info(data)

        return jsonify(data), response.status_code

    except requests.Timeout:
        return jsonify({
            "error": "Upstream request timed out",
            "developer": DEVELOPER,
            "telegram": TELEGRAM,
            "whatsapp": WHATSAPP
        }), 504

    except requests.RequestException as e:
        return jsonify({
            "error": "Upstream request failed",
            "details": str(e),
            "developer": DEVELOPER,
            "telegram": TELEGRAM,
            "whatsapp": WHATSAPP
        }), 502

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "developer": DEVELOPER,
            "telegram": TELEGRAM,
            "whatsapp": WHATSAPP
        }), 500


# Local development only.
# Vercel uses the Flask "app" object directly.
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
