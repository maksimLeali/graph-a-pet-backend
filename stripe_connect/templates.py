"""Server-rendered HTML for the Stripe Connect sample.

Plain Jinja2 template strings rendered with `flask.render_template_string`
(Jinja2 is already a Flask dependency — no new templates/ directory, no
new dependency). Jinja2 auto-escapes all variables, so product
names/descriptions/emails coming from Stripe or user input are safe to
interpolate directly.

Kept intentionally basic per the task ("clean, simple HTML with basic
styling") — this app has no existing server-rendered UI to match (the real
frontends are the separate Ionic/Next.js apps), so this borrows only the
inline-single-file-HTML convention already used for the GraphiQL page in
app.py.
"""

BASE_STYLE = """
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f4f4f5;
    color: #18181b;
  }
  .wrap { max-width: 720px; margin: 0 auto; padding: 32px 20px 64px; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  h2 { font-size: 17px; margin: 0 0 12px; }
  .sub { color: #71717a; font-size: 13px; margin: 0 0 24px; }
  .card {
    background: #fff;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
  }
  .row { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
  label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #3f3f46; }
  input, textarea {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #d4d4d8;
    border-radius: 6px;
    font-size: 14px;
    margin-bottom: 12px;
  }
  button, .btn {
    display: inline-block;
    background: #059669;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 9px 16px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
  }
  button:hover, .btn:hover { background: #047857; }
  .btn.secondary { background: #fff; color: #18181b; border: 1px solid #d4d4d8; }
  .btn.secondary:hover { background: #f4f4f5; }
  .pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .pill.green { background: #d1fae5; color: #065f46; }
  .pill.red { background: #fee2e2; color: #991b1b; }
  .pill.gray { background: #e4e4e7; color: #52525b; }
  .pill.amber { background: #fef3c7; color: #92400e; }
  .test-badge {
    display: inline-block;
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #f59e0b;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 20px;
  }
  ul.plain { list-style: none; padding: 0; margin: 0; }
  ul.plain li { padding: 10px 0; border-top: 1px solid #f0f0f1; }
  ul.plain li:first-child { border-top: none; }
  .muted { color: #71717a; font-size: 13px; }
  a { color: #059669; }
  .error {
    background: #fee2e2;
    border: 1px solid #fecaca;
    color: #991b1b;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 20px;
    font-size: 14px;
  }
</style>
"""

TEST_MODE_BANNER = (
	'<div class="test-badge">TEST MODE — no real money is processed</div>'
)

ERROR_PAGE = """
<!doctype html><html><head><meta charset="utf-8"><title>Stripe Connect sample — error</title>
""" + BASE_STYLE + """
</head><body><div class="wrap">
  <h1>Stripe Connect sample</h1>
  {{ test_badge|safe }}
  <div class="error"><strong>{{ title }}</strong><br>{{ message }}</div>
  <a class="btn secondary" href="{{ back_url }}">&larr; Back</a>
</div></body></html>
"""

INDEX_PAGE = """
<!doctype html><html><head><meta charset="utf-8"><title>Stripe Connect sample</title>
""" + BASE_STYLE + """
</head><body><div class="wrap">
  <h1>Stripe Connect sample</h1>
  <p class="sub">Onboard sellers, list their products, and let customers buy from a simple storefront.</p>
  {{ test_badge|safe }}

  <div class="card">
    <h2>Onboard a new seller</h2>
    <p class="muted">
      This creates a real (test-mode) Stripe V2 connected account and stores
      the mapping locally. In this demo a "seller" is just display name +
      email — a real integration would reuse whatever already represents a
      payee in your own app (e.g. a Shelter).
    </p>
    <form method="post" action="{{ create_seller_url }}">
      <label for="display_name">Display name</label>
      <input id="display_name" name="display_name" required placeholder="Jane's Pet Store">
      <label for="contact_email">Contact email</label>
      <input id="contact_email" name="contact_email" type="email" required placeholder="jane@example.com">
      <button type="submit">Create connected account</button>
    </form>
  </div>

  <div class="card">
    <h2>Sellers</h2>
    {% if sellers %}
    <ul class="plain">
      {% for seller in sellers %}
      <li class="row">
        <div>
          <strong>{{ seller.display_name }}</strong><br>
          <span class="muted">{{ seller.contact_email }} &middot; {{ seller.stripe_account_id }}</span>
        </div>
        <a class="btn secondary" href="{{ url_for('stripe_connect.seller_dashboard', seller_id=seller.id) }}">Manage</a>
      </li>
      {% endfor %}
    </ul>
    {% else %}
    <p class="muted">No sellers yet — create one above.</p>
    {% endif %}
  </div>
</div></body></html>
"""

SELLER_DASHBOARD_PAGE = """
<!doctype html><html><head><meta charset="utf-8"><title>{{ seller.display_name }} — dashboard</title>
""" + BASE_STYLE + """
</head><body><div class="wrap">
  <a class="muted" href="{{ url_for('stripe_connect.index') }}">&larr; All sellers</a>
  <h1>{{ seller.display_name }}</h1>
  <p class="sub">{{ seller.contact_email }} &middot; <span class="muted">{{ seller.stripe_account_id }}</span></p>
  {{ test_badge|safe }}

  <div class="card">
    <h2>Onboarding status</h2>
    <p>
      Capable of accepting payments:
      {% if status.ready_to_process_payments %}
        <span class="pill green">active</span>
      {% else %}
        <span class="pill red">not active</span>
      {% endif %}
    </p>
    <p>
      Onboarding:
      {% if status.onboarding_complete %}
        <span class="pill green">complete</span>
      {% else %}
        <span class="pill amber">{{ status.requirements_status or 'incomplete' }}</span>
      {% endif %}
    </p>
    {% if status.requirements and status.requirements|length %}
    <p class="muted">Outstanding requirements: {{ status.requirements|join(', ') }}</p>
    {% endif %}
    <p class="row">
      <a class="btn" href="{{ url_for('stripe_connect.start_onboarding', seller_id=seller.id) }}">
        {% if status.onboarding_complete %}Resume Stripe dashboard{% else %}Onboard to collect payments{% endif %}
      </a>
      <a class="btn secondary" href="{{ url_for('stripe_connect.seller_dashboard', seller_id=seller.id) }}">Refresh status</a>
    </p>
  </div>

  <div class="card">
    <h2>Products</h2>
    {% if products %}
    <ul class="plain">
      {% for p in products %}
      <li class="row">
        <div>
          <strong>{{ p.name }}</strong>
          {% if p.price %}<span class="muted"> &mdash; {{ p.price }}</span>{% endif %}
        </div>
      </li>
      {% endfor %}
    </ul>
    {% else %}
    <p class="muted">No products yet.</p>
    {% endif %}

    <h2 style="margin-top:20px">Create a product</h2>
    <form method="post" action="{{ url_for('stripe_connect.create_product', seller_id=seller.id) }}">
      <label for="name">Name</label>
      <input id="name" name="name" required placeholder="Bag of dog food">
      <label for="description">Description</label>
      <input id="description" name="description" placeholder="15kg, grain-free">
      <label for="price">Price (in whole dollars)</label>
      <input id="price" name="price" type="number" min="1" step="1" required placeholder="25">
      <button type="submit">Create product</button>
    </form>
  </div>

  <div class="card">
    <h2>Storefront</h2>
    <p class="muted">
      Public page customers use to buy from this seller. Uses the Stripe
      account id in the URL for this demo — use an opaque internal id
      instead in a real integration, not the raw Stripe account id.
    </p>
    <a class="btn secondary" href="{{ url_for('storefront.view_storefront', stripe_account_id=seller.stripe_account_id) }}">
      View storefront &rarr;
    </a>
  </div>

  <div class="card">
    <h2>Platform subscription (billed to this connected account)</h2>
    <p class="muted">
      Charges a platform-level plan directly to the connected account — V2
      accounts are their own Stripe customer, so no separate Customer
      object is needed.
    </p>
    {% if subscription %}
      <p>Status: <span class="pill {{ 'green' if subscription.status == 'active' else 'gray' }}">{{ subscription.status }}</span>
      {% if subscription.cancel_at_period_end %}<span class="muted"> (cancels at period end)</span>{% endif %}</p>
      <a class="btn secondary" href="{{ url_for('stripe_connect.billing_portal', seller_id=seller.id) }}">Manage subscription &rarr;</a>
    {% else %}
      <a class="btn" href="{{ url_for('stripe_connect.subscribe', seller_id=seller.id) }}">Subscribe to platform plan</a>
    {% endif %}
  </div>
</div></body></html>
"""

STOREFRONT_PAGE = """
<!doctype html><html><head><meta charset="utf-8"><title>Storefront</title>
""" + BASE_STYLE + """
</head><body><div class="wrap">
  <h1>Storefront</h1>
  <p class="sub">
    <!-- Demo-only: the connected account id (acct_...) is used directly in
         this URL for simplicity. Use an opaque store slug/internal id
         instead in a real integration — never expose acct_ ids to end
         customers. -->
    Shopping at <span class="muted">{{ stripe_account_id }}</span>
  </p>
  {{ test_badge|safe }}

  {% if products %}
  <div class="card">
    <ul class="plain">
      {% for p in products %}
      <li class="row">
        <div>
          <strong>{{ p.name }}</strong>
          {% if p.description %}<br><span class="muted">{{ p.description }}</span>{% endif %}
          {% if p.price_label %}<br><span class="muted">{{ p.price_label }}</span>{% endif %}
        </div>
        {% if p.price_id %}
        <form method="post" action="{{ url_for('storefront.checkout', stripe_account_id=stripe_account_id) }}">
          <input type="hidden" name="price_id" value="{{ p.price_id }}">
          <button type="submit">Buy</button>
        </form>
        {% endif %}
      </li>
      {% endfor %}
    </ul>
  </div>
  {% else %}
  <div class="card"><p class="muted">This seller has no products for sale yet.</p></div>
  {% endif %}
</div></body></html>
"""

SUCCESS_PAGE = """
<!doctype html><html><head><meta charset="utf-8"><title>Purchase complete</title>
""" + BASE_STYLE + """
</head><body><div class="wrap">
  <h1>Thanks!</h1>
  {{ test_badge|safe }}
  <div class="card">
    <p>Your (test) purchase was completed.</p>
    <p class="muted">Checkout session: {{ session_id }}</p>
  </div>
</div></body></html>
"""
