# crm-skills-openclaw

An [OpenClaw](https://github.com/openclaw/openclaw)-compatible skill that wraps the HubSpot CRM REST API, giving AI agents a clean JSON CLI interface for managing contacts, deals, companies, products, line items, and subscriptions.

This is phase 1 of a CRM skills monorepo. Phase 2 will add a Salesforce skill using the same patterns and shared type definitions.

---

## What is an OpenClaw skill?

OpenClaw skills are agent-callable CLI tools with a standard JSON output contract. Agents invoke them as subprocesses, parse stdout as JSON, and chain commands together to complete multi-step CRM workflows — no SDK integration required.

---

## Monorepo structure

```
hubspot-openclaw/
├── hubspot/               # HubSpot CRM skill (phase 1)
│   ├── SKILL.md           # OpenClaw skill definition
│   ├── pyproject.toml
│   └── src/hubspot_crm/
│       ├── cli.py
│       ├── client.py
│       ├── models.py
│       └── commands/
│           ├── contacts.py
│           ├── deals.py
│           ├── companies.py
│           ├── products.py
│           ├── line_items.py
│           └── subscriptions.py
├── shared/
│   └── types/
│       └── crm.py         # Shared Pydantic base models
└── salesforce/            # Phase 2 placeholder
```

---

## Prerequisites

- Python 3.11+
- A HubSpot Private App token ([create one here](https://app.hubspot.com/private-apps))

Required Private App scopes:
- `crm.objects.contacts` (read + write)
- `crm.objects.deals` (read + write)
- `crm.objects.companies` (read + write)
- `crm.objects.products` (read + write)
- `crm.objects.line_items` (read + write)

---

## Installation

```bash
pip install -e hubspot/
```

Set your token:

```bash
cp .env.example .env
# edit .env and add your token, then:
export HUBSPOT_ACCESS_TOKEN=pat-na1-...
```

---

## Usage

All commands output JSON to stdout. Success responses wrap data in `{"ok": true, "data": {...}}`. Errors return `{"ok": false, "error": "..."}` with a non-zero exit code.

### Contacts

```bash
hubspot-crm contacts list [--limit 20] [--after <cursor>]
hubspot-crm contacts get <id>
hubspot-crm contacts create --email foo@bar.com [--firstname Foo] [--lastname Bar] [--phone "+1..."] [--company Acme]
hubspot-crm contacts update <id> --phone "+1..."
hubspot-crm contacts delete <id>
hubspot-crm contacts search --email foo@bar.com
hubspot-crm contacts search --name "Alice"
```

### Deals

```bash
hubspot-crm deals list [--limit 20] [--after <cursor>]
hubspot-crm deals get <id>
hubspot-crm deals create --name "Acme Q3" --stage appointmentscheduled [--amount 5000] [--closedate 2025-12-31]
hubspot-crm deals update <id> --stage closedwon --amount 9500
hubspot-crm deals delete <id>
hubspot-crm deals associate <deal-id> --to contacts --id <contact-id>
hubspot-crm deals associate <deal-id> --to companies --id <company-id>
hubspot-crm deals associate <deal-id> --to line_items --id <line-item-id>
hubspot-crm deals search --name "Acme" --stage closedwon
```

Common deal stages: `appointmentscheduled`, `qualifiedtobuy`, `presentationscheduled`, `contractsent`, `closedwon`, `closedlost`

### Companies

```bash
hubspot-crm companies list
hubspot-crm companies get <id>
hubspot-crm companies create --name "Acme Corp" --domain acme.com
hubspot-crm companies update <id> --industry TECHNOLOGY
hubspot-crm companies delete <id>
hubspot-crm companies search --domain acme.com
```

### Products

```bash
hubspot-crm products list
hubspot-crm products get <id>
hubspot-crm products create --name "Enterprise Plan" --price 999 [--sku SKU-001]
hubspot-crm products update <id> --price 1199
hubspot-crm products delete <id>
```

### Line Items

```bash
hubspot-crm line-items list
hubspot-crm line-items get <id>
hubspot-crm line-items create --name "License" --quantity 5 --price 200 [--product-id <id>]
hubspot-crm line-items update <id> --quantity 10
hubspot-crm line-items delete <id>
hubspot-crm line-items associate <line-item-id> --deal-id <deal-id>
```

### Subscriptions

Requires [Commerce Hub](https://knowledge.hubspot.com/payments/get-started-with-commerce-hub).

```bash
hubspot-crm subscriptions list
hubspot-crm subscriptions get <id>
hubspot-crm subscriptions create --name "Pro Monthly" --mrr 199 --status active
hubspot-crm subscriptions update <id> --status cancelled
hubspot-crm subscriptions delete <id>
```

---

## Chaining commands

### Create a deal with a contact and line item

```bash
# Create contact
CONTACT_ID=$(hubspot-crm contacts create --email alice@acme.com --firstname Alice --lastname Smith \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# Create line item
LI_ID=$(hubspot-crm line-items create --name "Enterprise Seat" --quantity 5 --price 200 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# Create deal
DEAL_ID=$(hubspot-crm deals create --name "Acme Q3" --stage appointmentscheduled --amount 1000 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# Associate
hubspot-crm deals associate $DEAL_ID --to contacts --id $CONTACT_ID
hubspot-crm line-items associate $LI_ID --deal-id $DEAL_ID
```

### Paginate through all contacts

```bash
AFTER=""
while true; do
  ARGS="--limit 100"
  [ -n "$AFTER" ] && ARGS="$ARGS --after $AFTER"
  PAGE=$(hubspot-crm contacts list $ARGS)
  echo $PAGE | python3 -c "import sys,json; [print(r['properties'].get('email','')) for r in json.load(sys.stdin)['data']['results']]"
  AFTER=$(echo $PAGE | python3 -c "import sys,json; p=json.load(sys.stdin)['data'].get('paging'); print(p['next']['after'] if p else '')" 2>/dev/null)
  [ -z "$AFTER" ] && break
done
```

---

## Error handling

```python
import json, subprocess

result = json.loads(subprocess.check_output(["hubspot-crm", "contacts", "list", "--limit", "5"]))
if not result["ok"]:
    raise RuntimeError(result["error"])

for contact in result["data"]["results"]:
    print(contact["properties"]["email"])
```

---

## Development

```bash
# Install in editable mode
pip install -e hubspot/

# Run against your real HubSpot account
export HUBSPOT_ACCESS_TOKEN=pat-na1-...
hubspot-crm contacts list --limit 5

# Verify error handling (should fail cleanly)
unset HUBSPOT_ACCESS_TOKEN
hubspot-crm contacts list   # → {"ok": false, "error": "..."}, exit 1
```

---

## Phase 2: Salesforce skill

The `salesforce/` directory is a placeholder for a future skill using the same CLI shape but targeting Salesforce's REST API (SOQL search, Price Book for line items, OAuth 2.0 client credentials). The shared Pydantic types in `shared/types/crm.py` define the output schema both skills will conform to.

---

## License

MIT
