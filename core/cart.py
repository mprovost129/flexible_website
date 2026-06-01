"""
Session-based shopping cart.

Usage:
    cart = Cart(request)
    cart.add(product)
    cart.items(site)   -> list of dicts
    cart.total_cents(site)
    cart.clear()
"""


class Cart:
    SESSION_KEY = 'cbl_cart'

    def __init__(self, request):
        self.session = request.session
        self._data = dict(request.session.get(self.SESSION_KEY, {}))

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def add(self, product, quantity=1):
        key = str(product.pk)
        self._data[key] = self._data.get(key, 0) + quantity
        self._save()

    def update(self, product_id, quantity):
        key = str(product_id)
        if quantity <= 0:
            self._data.pop(key, None)
        else:
            self._data[key] = quantity
        self._save()

    def remove(self, product_id):
        self._data.pop(str(product_id), None)
        self._save()

    def clear(self):
        self._data = {}
        self._save()

    def _save(self):
        self.session[self.SESSION_KEY] = self._data
        self.session.modified = True

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def items(self, site):
        """Return a list of dicts: {product, quantity, subtotal_cents}."""
        from .models import Product
        result = []
        for pid_str, qty in list(self._data.items()):
            try:
                product = Product.objects.get(pk=int(pid_str), site=site, is_active=True)
            except (Product.DoesNotExist, ValueError):
                continue
            result.append({
                'product':        product,
                'quantity':       qty,
                'subtotal_cents': product.price_cents * qty,
                'subtotal_display': f'${product.price_cents * qty / 100:.2f}',
            })
        return result

    def total_cents(self, site):
        return sum(i['subtotal_cents'] for i in self.items(site))

    def count(self):
        return sum(self._data.values())

    def is_empty(self):
        return not self._data

    def line_items_for_stripe(self, site):
        """Build the line_items list for a Stripe Checkout Session."""
        result = []
        for item in self.items(site):
            p = item['product']
            result.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': p.name},
                    'unit_amount': p.price_cents,
                },
                'quantity': item['quantity'],
            })
        return result

    def snapshot(self, site):
        """Return a JSON-serialisable snapshot for Order.line_items."""
        return [
            {
                'product_id':   item['product'].pk,
                'name':         item['product'].name,
                'price_cents':  item['product'].price_cents,
                'quantity':     item['quantity'],
                'subtotal_cents': item['subtotal_cents'],
            }
            for item in self.items(site)
        ]
