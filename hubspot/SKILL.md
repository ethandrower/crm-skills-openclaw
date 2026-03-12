---
name: hubspot-crm
description: Manage HubSpot CRM objects (contacts, deals, companies, products, line items, subscriptions) via CLI
version: 1.0.0
metadata:
  openclaw:
    requires:
      env: [HUBSPOT_ACCESS_TOKEN]
      bins: [hubspot-crm]
    primaryEnv: HUBSPOT_ACCESS_TOKEN
    emoji: "🟠"
---

# HubSpot CRM Skill

This skill provides a CLI interface to the HubSpot CRM API. All commands output JSON to stdout so agents can parse results programmatically.

## Authentication

Set `HUBSPOT_ACCESS_TOKEN` to your HubSpot Private App token before running any command:

```bash
export HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

To create a Private App token: HubSpot → Settings → Integrations → Private Apps → Create.
Required scopes: `crm.objects.contacts`, `crm.objects.deals`, `crm.objects.companies`,
`crm.objects.products`, `crm.objects.line_items`.

If the token is missing the CLI prints a clear error and exits with code 1.

## Output Format

All commands return JSON on stdout:

- **Success**: `{"ok": true, "data": { ... }}`
- **Error**: `{"ok": false, "error": "message"}`

List commands include a `paging` field for cursor-based pagination:

```json
{
  "ok": true,
  "data": {
    "results": [...],
    "paging": {"next": {"after": "cursor-token"}}
  }
}
```

Pass `--after <cursor>` to fetch the next page.

---

## Commands

### contacts

```bash
hubspot-crm contacts list [--limit 20] [--after <cursor>] [--properties email,firstname]
hubspot-crm contacts get <id>
hubspot-crm contacts create --email foo@bar.com [--firstname Foo] [--lastname Bar] [--phone "+1555..."] [--company Acme]
hubspot-crm contacts update <id> [--email ...] [--firstname ...] [--lastname ...] [--phone ...] [--company ...]
hubspot-crm contacts delete <id>
hubspot-crm contacts search [--email foo@bar.com] [--name "John"] [--limit 10]
```

### deals

```bash
hubspot-crm deals list [--limit 20] [--after <cursor>]
hubspot-crm deals get <id>
hubspot-crm deals create --name "Acme Q3" --stage appointmentscheduled [--amount 5000] [--closedate 2025-12-31] [--pipeline default]
hubspot-crm deals update <id> [--name ...] [--stage ...] [--amount ...] [--closedate ...]
hubspot-crm deals delete <id>
hubspot-crm deals associate <deal-id> --to contacts --id <contact-id>
hubspot-crm deals associate <deal-id> --to companies --id <company-id>
hubspot-crm deals associate <deal-id> --to line_items --id <line-item-id>
hubspot-crm deals search [--name "Acme"] [--stage appointmentscheduled] [--limit 10]
```

Common deal stages: `appointmentscheduled`, `qualifiedtobuy`, `presentationscheduled`,
`decisionmakerboughtin`, `contractsent`, `closedwon`, `closedlost`

### companies

```bash
hubspot-crm companies list [--limit 20] [--after <cursor>]
hubspot-crm companies get <id>
hubspot-crm companies create --name "Acme Corp" [--domain acme.com] [--industry TECHNOLOGY] [--phone "+1555..."]
hubspot-crm companies update <id> [--name ...] [--domain ...] [--industry ...] [--phone ...]
hubspot-crm companies delete <id>
hubspot-crm companies search [--domain acme.com] [--name "Acme"] [--limit 10]
```

### products

```bash
hubspot-crm products list [--limit 20] [--after <cursor>]
hubspot-crm products get <id>
hubspot-crm products create --name "Enterprise Plan" [--price 999.00] [--description "..."] [--sku SKU-001]
hubspot-crm products update <id> [--name ...] [--price ...] [--description ...] [--sku ...]
hubspot-crm products delete <id>
```

### line-items

```bash
hubspot-crm line-items list [--limit 20] [--after <cursor>]
hubspot-crm line-items get <id>
hubspot-crm line-items create --name "License" --quantity 1 --price 500 [--product-id <hs-product-id>]
hubspot-crm line-items update <id> [--name ...] [--quantity ...] [--price ...]
hubspot-crm line-items delete <id>
hubspot-crm line-items associate <line-item-id> --deal-id <deal-id>
```

### subscriptions

Requires Commerce Hub. Uses `crm/v3/objects/subscriptions` internally.

```bash
hubspot-crm subscriptions list [--limit 20] [--after <cursor>]
hubspot-crm subscriptions get <id>
hubspot-crm subscriptions create --name "Pro Monthly" [--mrr 199.00] [--status active] [--start-date 2025-01-01] [--end-date 2025-12-31]
hubspot-crm subscriptions update <id> [--name ...] [--mrr ...] [--status ...] [--end-date ...]
hubspot-crm subscriptions delete <id>
```

---

## Chaining Examples

### Create a deal and associate a contact

```bash
# 1. Create or find the contact
CONTACT=$(hubspot-crm contacts create --email alice@acme.com --firstname Alice --lastname Smith)
CONTACT_ID=$(echo $CONTACT | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# 2. Create the deal
DEAL=$(hubspot-crm deals create --name "Acme Q3" --stage appointmentscheduled --amount 10000)
DEAL_ID=$(echo $DEAL | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# 3. Associate
hubspot-crm deals associate $DEAL_ID --to contacts --id $CONTACT_ID
```

### Add a line item to a deal

```bash
# 1. Create the line item
LI=$(hubspot-crm line-items create --name "Enterprise Seat" --quantity 5 --price 200)
LI_ID=$(echo $LI | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# 2. Associate it with the deal
hubspot-crm line-items associate $LI_ID --deal-id $DEAL_ID
```

### Paginate through all contacts

```bash
AFTER=""
while true; do
  ARGS="--limit 100"
  [ -n "$AFTER" ] && ARGS="$ARGS --after $AFTER"
  PAGE=$(hubspot-crm contacts list $ARGS)
  echo $PAGE | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; [print(r['properties'].get('email','')) for r in d['results']]"
  AFTER=$(echo $PAGE | python3 -c "import sys,json; p=json.load(sys.stdin)['data'].get('paging'); print(p['next']['after'] if p else '')" 2>/dev/null)
  [ -z "$AFTER" ] && break
done
```

---

## Error Handling

Always check `ok` before using `data`:

```python
import json, subprocess
result = json.loads(subprocess.check_output(["hubspot-crm", "contacts", "list"]))
if not result["ok"]:
    raise RuntimeError(result["error"])
contacts = result["data"]["results"]
```
