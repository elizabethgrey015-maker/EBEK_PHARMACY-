from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Drug, Sale
from . import db
from datetime import datetime
import json

views = Blueprint('views', __name__)

@views.route('/', methods=['GET'])
@login_required
def home():
    # POS TERMINAL - always show drugs even if 0
    drugs = Drug.query.all()
    return render_template("pos.html", drugs=drugs, user=current_user)

@views.route('/inventory')
@login_required
def inventory():
    drugs = Drug.query.all()
    return render_template("inventory.html", drugs=drugs, user=current_user)

@views.route('/add-drug', methods=['GET','POST'])
@login_required
def add_drug():
    if request.method == 'POST':
        try:
            name = (request.form.get('name') or '').strip()
            category = (request.form.get('category') or 'General').strip()
            price = float(request.form.get('price') or 0)
            stock = int(request.form.get('stock') or 0)
            if not name:
                flash('Drug name required', 'error')
            elif Drug.query.filter_by(name=name).first():
                flash(f'{name} already exists!', 'error')
            else:
                db.session.add(Drug(name=name, category=category, price=price, stock=stock))
                db.session.commit()
                flash(f'{name} added!', 'success')
                return redirect(url_for('views.inventory'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
    return render_template("add_drug.html", user=current_user)

@views.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_data = request.form.get('cart_data')
    if not cart_data or cart_data == '[]' or cart_data == '':
        flash('Cart empty!', 'error')
        return redirect(url_for('views.home'))
    try:
        cart = json.loads(cart_data)
        total = 0.0
        for item in cart:
            # safe get
            drug_id = item.get('id')
            qty = int(item.get('qty', 0))
            drug = Drug.query.get(drug_id)
            if drug and drug.stock is not None and drug.stock >= qty:
                drug.stock -= qty
                total += qty * float(drug.price or 0)
        db.session.commit()
        if total > 0:
            db.session.add(Sale(total=total, date=datetime.now()))
            db.session.commit()
            flash(f'Sale Success! GHS {total:.2f}', 'success')
        else:
            flash('No sale recorded', 'error')
    except Exception as e:
        flash(f'Checkout error: {e}', 'error')
    return redirect(url_for('views.home'))

@views.route('/sales')
@login_required
def sales():
    sales = Sale.query.order_by(Sale.date.desc()).all()
    total_revenue = sum(float(s.total or 0) for s in sales)
    current_date = datetime.now().strftime("%d %B %Y")
    return render_template("sales.html", sales=sales, total_revenue=total_revenue, current_date=current_date, user=current_user)

@views.route('/delete-drug/<int:id>')
@login_required
def delete_drug(id):
    drug = Drug.query.get(id)
    if drug:
        db.session.delete(drug)
        db.session.commit()
        flash(f'{drug.name} deleted', 'success')
    return redirect(url_for('views.inventory'))

from flask import jsonify

@views.route('/sync-offline', methods=['POST'])
@login_required
def sync_offline():
    try:
        data = request.get_json()
        cart = data.get('cart', [])
        total = float(data.get('total', 0))
        # Deduct stock again
        for item in cart:
            drug = Drug.query.get(item.get('id'))
            if drug and drug.stock >= item.get('qty',0):
                drug.stock -= item.get('qty',0)
        sale = Sale(total=total, date=datetime.now())
        db.session.add(sale)
        db.session.commit()
        return jsonify({"status":"synced"}), 200
    except Exception as e:
        return jsonify({"error":str(e)}), 400