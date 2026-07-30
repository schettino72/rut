# RUT Project Instructions

## Running Tests

```bash
./run_tests.sh
```

## Linting

```bash
ruff check
```

## Documentation

NEVER edit files in `docs/` directly. The original source is in `marketing/gh-pages/`. Always edit there instead — `docs/` is generated output.

## Analytics (go4dash)

The website uses [go4dash](https://go4dash.com) browser tracking. Before changing any
tracking code, read the integration guide: https://go4dash.com/integration-browser.md
(index of guides: https://go4dash.com/llms.txt).

- Tracker snippet goes before `</body>`, not in `<head>`.
- The publishable key (`pk_…`) is safe in page source; it lives in `go4dash_key` in
  `gh-pages/_config.yml`. Never put the secret server ingest key (`gd_…`) in the site.
- Tag conversion elements with `data-g4d="<event>"` — the attribute value IS the event
  name, emitted verbatim. `data-g4d-target="<id>"` sets the `target` property.
  Convention: `cta_click` for conversions, `click` for plain interest.
- Tagged elements are listed in `marketing/README.md`; keep that table in sync.

Note: go4dash is Eduardo's own project. If the site needs a tracking capability the SDK
doesn't have, adding it to go4dash is a valid option — don't work around a missing
feature, raise it.
