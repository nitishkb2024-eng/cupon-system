
from flask import Flask, request, jsonify, render_template
from datetime import date

app = Flask(__name__)
coupons = {}


def validate_rules(coupon, amount=None):
    if coupon is None:
        return "Coupon does not exist"

    if not coupon["active"]:
        return "Coupon is inactive"

    if coupon["expiry"]:
        try:
            expiry_date = date.fromisoformat(coupon["expiry"])
        except (ValueError, TypeError):
            return "Invalid expiry date"

        if expiry_date < date.today():
            return "Coupon has expired"

    if coupon["used"] >= coupon["usage_limit"]:
        return "Coupon usage limit reached"

    if amount is not None and amount < coupon["minimum_amount"]:
        return "Purchase amount is below the minimum required"

    return None


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/coupons")
def list_coupons():
    return jsonify({
        "count": len(coupons),
        "coupons": [
            {"code": code, **coupon}
            for code, coupon in coupons.items()
        ]
    })


@app.post("/coupons")
def add_coupon():
    data = request.get_json(silent=True) or {}
    code = str(data.get("code", "")).strip().upper()

    try:
        discount = float(data.get("discount", 0))
        minimum = float(data.get("minimum_amount", 0))
        usage_limit = int(data.get("usage_limit", 10))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric value"}), 400

    expiry = data.get("expiry") or None

    if not code:
        return jsonify({"error": "Coupon code is required"}), 400

    if not 0 < discount <= 100:
        return jsonify({"error": "Discount must be greater than 0 and at most 100"}), 400

    if minimum < 0:
        return jsonify({"error": "Minimum amount cannot be negative"}), 400

    if usage_limit < 1:
        return jsonify({"error": "Usage limit must be at least 1"}), 400

    if code in coupons:
        return jsonify({"error": "Coupon already exists"}), 409

    if expiry:
        try:
            date.fromisoformat(expiry)
        except (ValueError, TypeError):
            return jsonify({"error": "Expiry must use YYYY-MM-DD"}), 400

    coupons[code] = {
        "discount": discount,
        "minimum_amount": minimum,
        "expiry": expiry,
        "active": True,
        "usage_limit": usage_limit,
        "used": 0
    }

    return jsonify({
        "message": "Coupon created successfully",
        "coupon": {"code": code, **coupons[code]}
    }), 201


@app.get("/coupons/<code>/validate")
def validate_coupon(code):
    code = code.strip().upper()
    coupon = coupons.get(code)
    error = validate_rules(coupon)

    if error:
        return jsonify({"valid": False, "message": error}), 400

    return jsonify({
        "valid": True,
        "message": "Coupon is valid",
        "code": code,
        "discount": coupon["discount"],
        "minimum_amount": coupon["minimum_amount"],
        "expiry": coupon["expiry"],
        "remaining_uses": coupon["usage_limit"] - coupon["used"]
    })


@app.post("/coupons/<code>/apply")
def apply_coupon(code):
    code = code.strip().upper()
    coupon = coupons.get(code)
    data = request.get_json(silent=True) or {}

    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Amount must be numeric"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero"}), 400

    error = validate_rules(coupon, amount)

    if error:
        return jsonify({"error": error}), 400

    discount_amount = round(amount * coupon["discount"] / 100, 2)
    final_amount = round(amount - discount_amount, 2)

    # Count a use only after a successful application.
    coupon["used"] += 1

    return jsonify({
        "message": "Coupon applied successfully",
        "code": code,
        "original_amount": round(amount, 2),
        "discount_percentage": coupon["discount"],
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "used": coupon["used"],
        "remaining_uses": coupon["usage_limit"] - coupon["used"]
    })


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "Coupon System",
        "version": "v3"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
