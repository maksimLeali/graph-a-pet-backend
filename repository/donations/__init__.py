"""Graph-a-Pet donation domain — repository layer.

Split into submodules by concern (accounts.py, funding_needs.py, limits.py,
donations.py, ledger.py, expenses.py, webhook_events.py, payment_profiles.py)
rather than one flat file, since this bounded context has 10+ models.
`domain/donations/` imports these directly, e.g.
`import repository.donations.accounts as accounts_data`.
"""
