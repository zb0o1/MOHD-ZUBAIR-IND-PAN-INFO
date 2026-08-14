from flask import Flask, request, jsonify

app = Flask(__name__)


@app.get("/")
def home():
    return jsonify({
        "status": "online",
        "message": "API working"
    })


@app.get("/pan-info")
def pan_info():
    pan = request.args.get("pan", "").strip().upper()

    if len(pan) != 10:
        return jsonify({
            "error": "PAN parameter must contain 10 characters"
        }), 400

    return jsonify({
        "status": "success",
        "message": "Vercel API is working",
        "pan_received": pan
    })


if __name__ == "__main__":
    app.run()
