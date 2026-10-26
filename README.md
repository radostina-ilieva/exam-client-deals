# Client Deals

A Django web application for pricing TV advertising deals. It stores the yearly
price conditions, calculates the price of a deal for a chosen target group, and
saves the result as an **offer** for a client.

> This project was created as a Django Basics exam project. All data in the
> examples is fictitious.

## What the application does

1. **Clients** are grouped by **sector**.
2. **Pricing conditions are set once per pricing year**: base price per target
   group, prime time and channel split indexes, and 12 monthly coefficients.
3. The **price calculator** turns those conditions into a full price breakdown.
4. An **offer** ties a client to one calculation and keeps a **snapshot** of the
   calculated prices, so an old offer never changes when the conditions of a
   year are edited later.

## Technology

- Python and Django
- SQLite (default database, no setup needed)
- Bootstrap 5 (CSS only) and a custom stylesheet (`static/css/style.css`)
- Django Template Engine with a base template and partial templates
- No JavaScript is used anywhere in the project

## Features

### Clients and sectors (`clients`)

- Full create, read, update, delete for clients and sectors.
- Search by name, pagination, and a detail page per client and per sector.
- The client page lists all clients and sectors assigned to them.
- A sector that still has clients cannot be deleted.

### Pricing setup (`pricing`)

- **Pricing years**: one record per year, with a readiness overview (how many
  prices, monthly coefficients and index bands each year has).
- **Channels** and **target groups**. Every target group is linked to the
  channels it can be sold on (many-to-many).
- **Base prices**: one price per target group and year, with filtering by year
  and group and sorting by group, price or year.
- **Monthly coefficients**: all 12 months of a year are edited on one page.
- **Index bands** for two index types: *Prime time* and *Channel split*.
- A guided home page (`/pricing/`) lists the setup steps with live counters.

### Price calculator (`pricing`)

The calculator shows every step of the price:

```text
Base price                  (year + target group)
x Prime time index          (looked up by the prime time %)
x Channel split index       (looked up by the main channel %)
= Adjusted price
x Monthly coefficient       -> price for each of the 12 months
Average of the 12 months    -> average year price (rounded to 2 decimals)
```

**Index bands.** Each band stores an upper limit ("up to X%") and a
coefficient. For a given percentage the calculator uses the band with the
smallest upper limit that is greater than or equal to the percentage. Every
year needs a band with an upper limit of 100 for each index type.

**Example (fictitious numbers).** Base price 285.00, prime time 55 % (index
1.00), channel split 70 % (index 1.00), monthly coefficients
1.00, 1.15, 1.30, 1.35, 1.35, 1.35, 1.00, 1.00, 1.30, 1.50, 1.50, 1.30:
the adjusted price is 285.00 and the average year price is **358.63**.

If something is missing (no base price, no band, a missing month), the
calculator shows a clear message instead of failing.

### Offers (`deals`)

- Create an offer for a client, a pricing year and a target group, with the
  prime time % and the main channel %.
- The price is calculated when the offer is saved and stored as a snapshot
  (base price, both indexes, adjusted price, average price).
- List with filters (year, target group) and sorting, detail page, edit and
  delete with confirmation.
- Only the **status** (Draft, Sent, Accepted, Rejected) and the **notes** can be
  edited. To change the calculation, create a new offer.

## Project structure

```text
.
├── ExamClientDeals/     Django project: settings and root URLs
├── general/             Home page and shared view/form mixins
├── clients/             Sector and Client models, forms, views
├── pricing/             Pricing models, calculator service, forms, views,
│                        custom exceptions and template tags
├── deals/               Offer model, forms and views
├── templates/           base.html, home.html, 404.html, calculator.html,
│   ├── partials/        navigation, footer, form fields, pagination,
│   │                    price breakdown
│   └── ...              one folder per section (clients, sectors, years,
│                        channels, groups, prices, bands, deals, pricing)
├── static/css/          style.css
├── manage.py
└── requirements.txt
```

The price logic lives in `pricing/services.py` and does not depend on views or
templates. Both the calculator page and the offer form use the same function.

## Getting started

Requirements: Python 3 and `pip`.

**No environment variables are required.** The project runs with its default
settings and a local SQLite database.

### 1. Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install the dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Create the database

```bash
python manage.py migrate
```

### 4. Run the application

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser.

The database starts **empty**. No sample data is included, everything is created
through the application.

## First-time data setup

Follow these steps in order (the page `/pricing/` shows the same list with
counters):

1. Create a **pricing year**, for example 2027.
2. Create one or more **channels**.
3. Create **target groups** and choose their channels.
4. Add a **base price** for a target group and the year.
5. Open the year and enter the **12 monthly coefficients** (between 0.80 and 2.50).
6. Add **index bands** for *Prime time* and for *Channel split*. Include a band
   with an upper limit of 100 for each type.
7. Create a **sector** and a **client**.
8. Open the **price calculator**, then create an **offer**.

## Main pages

| Page | URL |
|---|---|
| Home | `/` |
| Clients | `/clients/` |
| Sectors | `/clients/sectors/` |
| Pricing setup | `/pricing/` |
| Pricing years | `/pricing/years/` |
| Channels | `/pricing/channels/` |
| Target groups | `/pricing/target-groups/` |
| Base prices | `/pricing/prices/` |
| Index bands | `/pricing/index-bands/` |
| Price calculator | `/pricing/calculator/` |
| Offers | `/deals/` |

## Technical notes

- **Models and relations.** Many-to-one: client to sector, offer to client,
  year and target group, price to year and target group. Many-to-many: target
  group to channels. Unique and check constraints protect the data
  (for example one price per target group and year, percentages between 0 and
  100).
- **Money and coefficients** use `DecimalField` and `Decimal`, never floats. The
  average price is rounded half up.
- **Forms** validate input and show custom labels, help texts and error
  messages. Delete forms and the offer edit form use read-only (disabled)
  fields.
- **Class-based views** with shared mixins: `DisableFieldsMixin`,
  `GetFormInstanceMixin`, `ProtectedDeleteMixin`, `FilterQueryMixin`.
- **Protected deletes.** Records that are still used (a year with prices, a
  client with offers, and so on) cannot be deleted, and the user sees a message.
- **Templates.** One base template, reusable partials, a custom 404 page, and
  custom template tags and filters (`money`, `percent`, `month_name`).
- **Custom exceptions** (`PricingError` and its subclasses) turn missing pricing
  data into readable form errors.

## Limitations and ideas for the future

- No user accounts or permissions yet.
- Offers hold one calculation each, without a month-by-month table.
- Discounts, bonuses and agencies are not part of this version.
- Automated tests are planned.
- Before any real deployment: set `DEBUG = False`, configure `ALLOWED_HOSTS`,
  load the `SECRET_KEY` from the environment, and use a production database.
