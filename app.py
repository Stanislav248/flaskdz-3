import json
import re
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "change-me-in-production"

ORDERS_FILE = Path(__file__).parent / "orders.json"
DELIVERY_FEE = 60       # грн
FREE_DELIVERY_FROM = 500  # грн

CATEGORIES = ["Піца", "Паста", "Десерти", "Напої"]

MENU = [
    {"id": 1, "name": "Маргарита", "category": "Піца", "price": 195, "emoji": "🍕",
     "desc": "Томати, моцарела, свіжий базилік"},
    {"id": 2, "name": "Пепероні", "category": "Піца", "price": 235, "emoji": "🍕",
     "desc": "Гостра салямі пепероні, моцарела, томатний соус"},
    {"id": 3, "name": "Чотири сири", "category": "Піца", "price": 255, "emoji": "🧀",
     "desc": "Моцарела, горгонзола, пармезан, чеддер"},
    {"id": 4, "name": "Карбонара", "category": "Паста", "price": 215, "emoji": "🍝",
     "desc": "Спагеті, гуанчале, жовток, пекоріно"},
    {"id": 5, "name": "Болоньєзе", "category": "Паста", "price": 205, "emoji": "🍝",
     "desc": "Тальятелле з повільно тушкованим м'ясним рагу"},
    {"id": 6, "name": "Пенне арабіата", "category": "Паста", "price": 175, "emoji": "🌶️",
     "desc": "Пенне, томати, часник, чилі"},
    {"id": 7, "name": "Тірамісу", "category": "Десерти", "price": 125, "emoji": "🍰",
     "desc": "Савоярді, маскарпоне, еспресо, какао"},
    {"id": 8, "name": "Панна котта", "category": "Десерти", "price": 110, "emoji": "🍮",
     "desc": "Вершковий десерт з ягідним соусом"},
    {"id": 9, "name": "Лимонад", "category": "Напої", "price": 70, "emoji": "🍋",
     "desc": "Домашній лимонад з м'ятою"},
    {"id": 10, "name": "Еспресо", "category": "Напої", "price": 55, "emoji": "☕",
     "desc": "Класичний італійський еспресо"},
]
MENU_BY_ID = {item["id"]: item for item in MENU}


def load_orders():
    if ORDERS_FILE.exists():
        try:
            return json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def save_order(order):
    orders = load_orders()
    order["id"] = len(orders) + 1
    orders.append(order)
    ORDERS_FILE.write_text(json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8")
    return order["id"]


def parse_cart(raw):
    """Перебудовує кошик із JSON, а ціни беремо з MENU (клієнту не довіряємо)."""
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return [], 0
    items, total = [], 0
    for row in data:
        try:
            dish = MENU_BY_ID[int(row["id"])]
            qty = max(1, min(int(row["qty"]), 20))
        except (KeyError, ValueError, TypeError):
            continue
        items.append({"id": dish["id"], "name": dish["name"], "qty": qty, "price": dish["price"]})
        total += dish["price"] * qty
    return items, total


def validate(form):
    errors = {}
    name = form.get("name", "").strip()
    phone = form.get("phone", "").strip()
    street = form.get("street", "").strip()

    if len(name) < 2:
        errors["name"] = "Вкажіть ім'я (мінімум 2 символи)."
    digits = re.sub(r"\D", "", phone)
    if not 10 <= len(digits) <= 12:
        errors["phone"] = "Введіть номер телефону, наприклад +380 67 123 45 67."
    if len(street) < 3:
        errors["street"] = "Вкажіть вулицю та номер будинку."
    return errors


@app.route("/")
def index():
    return render_template("index.html", menu=MENU, categories=CATEGORIES)


@app.route("/delivery", methods=["GET", "POST"])
def delivery():
    errors, values = {}, {}
    if request.method == "POST":
        values = request.form.to_dict()
        errors = validate(request.form)
        items, subtotal = parse_cart(request.form.get("cart"))
        if not items:
            errors["cart"] = "Кошик порожній. Додайте страви з меню."
        if not errors:
            fee = 0 if subtotal >= FREE_DELIVERY_FROM else DELIVERY_FEE
            order_id = save_order({
                "created": datetime.now().isoformat(timespec="seconds"),
                "name": values["name"].strip(),
                "phone": values["phone"].strip(),
                "street": values["street"].strip(),
                "apartment": values.get("apartment", "").strip(),
                "comment": values.get("comment", "").strip(),
                "time": values.get("time", "asap"),
                "payment": values.get("payment", "cash"),
                "items": items,
                "subtotal": subtotal,
                "fee": fee,
                "total": subtotal + fee,
            })
            return redirect(url_for("success", order_id=order_id))
    return render_template(
        "delivery.html",
        errors=errors,
        values=values,
        menu_by_id=MENU_BY_ID,
        fee=DELIVERY_FEE,
        free_from=FREE_DELIVERY_FROM,
    )


@app.route("/success/<int:order_id>")
def success(order_id):
    order = next((o for o in load_orders() if o["id"] == order_id), None)
    if order is None:
        abort(404)
    return render_template("success.html", order=order)


if __name__ == "__main__":
    app.run(debug=True)
