
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# In-memory storage for v1
coupons = {}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/coupons", methods=["GET"])
def list_coupons():
    return jsonify({
        "count": len(coupons),
        "coupons": [
            {"code": code, **coupon}
            for code, coupon in coupons.items()
        ]
    }), 200


@app.route("/coupons", methods=["POST"])
def add_coupon():
    data = request.get_json(silent=True) or {}

    code = str(data.get("code", "")).strip().upper()

    try:
        discount = float(data.get("discount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Discount must be a number"}), 400

    if not code:
        return jsonify({"error": "Coupon code is required"}), 400

    if not 0 < discount <= 100:
        return jsonify({
            "error": "Discount must be greater than 0 and at most 100"
        }), 400

    if code in coupons:
        return jsonify({"error": "Coupon already exists"}), 409

    coupons[code] = {
        "discount": discount,
        "active": True
    }

    return jsonify({
        "message": "Coupon created successfully",
        "coupon": {"code": code, **coupons[code]}
    }), 201


@app.route("/coupons/<code>/validate", methods=["GET"])
def validate_coupon(code):
    code = code.strip().upper()
    coupon = coupons.get(code)

    if not coupon or not coupon["active"]:
        return jsonify({
            "valid": False,
            "message": "Coupon is invalid or inactive"
        }), 404

    return jsonify({
        "valid": True,
        "message": "Coupon is valid",
        "code": code,
        "discount": coupon["discount"]
    }), 200


@app.route("/coupons/<code>/apply", methods=["POST"])
def apply_coupon(code):
    code = code.strip().upper()
    coupon = coupons.get(code)

    if not coupon or not coupon["active"]:
        return jsonify({"error": "Invalid or inactive coupon"}), 404

    data = request.get_json(silent=True) or {}

    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Amount must be a number"}), 400

    if amount <= 0:
        return jsonify({
            "error": "Purchase amount must be greater than zero"
        }), 400

    discount_amount = round(amount * coupon["discount"] / 100, 2)

    return jsonify({
        "message": "Coupon applied successfully",
        "code": code,
        "original_amount": round(amount, 2),
        "discount_percentage": coupon["discount"],
        "discount_amount": discount_amount,
        "final_amount": round(amount - discount_amount, 2)
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "application": "Coupon System",
        "version": "v1"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
