# Demo Project — Mini Finance Tracker

Self-contained demo project for recording asciinema demos of the rut CLI.

Uses a mini personal finance tracker (accounts, currencies, transfers, reports)
with ~20 unittest tests across 4 test modules.

## Why a dedicated demo?

Using a real project would break when code changes. This project is stable,
reproducible, and designed to showcase rut features.

## Running

```bash
cd demo
rut            # dot output, all pass
rut -v         # full test names
rut -k "transfer"  # keyword filtering
rut --cov      # coverage report
rut --changed  # incremental (modify a file first)
```

## Structure

```
finance/
├── currency.py      # exchange rates, convert()
├── account.py       # Account class — deposit, withdraw, balance_in()
├── transaction.py   # transfer between accounts
└── report.py        # net worth, summary

tests/
├── test_currency.py      # 6 tests
├── test_account.py       # 5 tests
├── test_transaction.py   # 5 tests
└── test_report.py        # 4 tests
```

## Recording

See [movie-script.md](movie-script.md) for the exact commands, break/fix
sequences, and narration notes for each demo recording.

## Notes

Source modules include small `time.sleep()` calls to simulate I/O (rate lookups,
transaction processing, report aggregation). This gives realistic timing (~0.5s)
instead of instant results that make a test runner demo look pointless.
