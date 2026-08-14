import os
import re
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
UPSTREAM_URL = os.getenv("UPSTREAM_URL", "").strip()
UPSTREAM_TOKEN = os.getenv("UPSTREAM_TOKEN", "").strip()

PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def error_response(message, status=400, **extra):
    payload = {
        "error": message
    }
    payload.update(extra)
    return jsonify(payload), status


def validate_pan(value):
    pan = (value or "").strip().upper()

    if not PAN_PATTERN.fullmatch(pan):
        return None

    return pan


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------
@app.get("/")
def home():
    return jsonify({
        "api": "PAN Info API",
        "status": "online"
    })


# ---------------------------------------------------------
# PAN endpoint
# ---------------------------------------------------------
@app.get("/pan-info")
def pan_info():

    pan = validate_pan(request.args.get("pan"))

    if not pan:
        return error_response(
            "Valid PAN format required",
            400
        )

    if not UPSTREAM_URL:
        return error_response(
            "UPSTREAM_URL is not configured",
            500
        )

    if not UPSTREAM_TOKEN:
        return error_response(
            "UPSTREAM_TOKEN is not configured",
            500
        )

    headers = {
        "Authorization": f"Bearer {UPSTREAM_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(
            UPSTREAM_URL,
            params={"pan": pan},
            headers=headers,
            timeout=15,
        )

        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        if "application/json" in content_type:
            try:
                data = response.json()
            except ValueError:
                return error_response(
                    "Upstream returned invalid JSON",
                    502
                )
        else:
            return error_response(
                "Upstream returned a non-JSON response",
                502,
                upstream_status=response.status_code
            )

        return jsonify(data), response.status_code

    except requests.Timeout:
        return error_response(
            "Upstream request timed out",
            504
        )

    except requests.ConnectionError:
        return error_response(
            "Could not connect to upstream service",
            502
        )

    except requests.RequestException:
        return error_response(
            "Upstream request failed",
            502
        )

    except Exception:
        return error_response(
            "Internal server error",
            500
        )


# ---------------------------------------------------------
# Local development
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
