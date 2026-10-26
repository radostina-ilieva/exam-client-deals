# Client Deal App.

**A Django web application for managing clients, pricing data, and
commercial offers. It includes a pricing calculator that shows price breakdown.**

## Features

### Client and Sector management

-   Create, view, edit, and delete clients and sectors.
-   Organize clients by sector.
-   View sector details and the number of clients associated with each
    sector.
-   Prevent deletion of records that are still referenced by other
    records where the data model requires protection.

### Pricing configuration

-   Manage pricing years.
-   Manage channels and target groups.
-   Associate channels with target groups.
-   Maintain base prices for target groups by pricing year.
-   Configure monthly coefficients for each pricing year.
-   Configure index bands for Prime Time and Channel Split indexes.

### Price calculator

The calculator uses the following approach:

``` text
Base price = calculator gets the price according to: year, target group, prime time % and channel split %
Adjusted price = Base price × Prime Time index × Channel Split index
Monthly price  = Adjusted price × Monthly coefficient
Average price  = Average of the 12 monthly prices
```

The calculator validates the supplied percentages and requires a base
price, index bands, and all 12 monthly coefficients for the selected
pricing year.

### Offer management

-   Create offers for clients using a pricing year and target group.
-   Save the selected Prime Time and main-channel percentages.
-   Store a snapshot of the calculated pricing values on the offer.
-   List offers and view individual offer details.
-   Edit offer status and notes.
-   Delete offers after confirmation.

Offer pricing is stored as a snapshot when the offer is created. Editing
an offer does not automatically recalculate its stored prices.

## Technology stack

-   Python
-   Django
-   SQLite (default development database)
-   Bootstrap 5
-   HTML and CSS

The project styling is maintained in `static/css/style.css`. The
interface uses a teal-based palette, with `#004F5A` as the primary
color. The project does not require JavaScript for its Django views or
CSS styling.

## Project structure

``` text
.
├── ExamClientDeals/       # Django project settings and root URL configuration
├── clients/               # Client and sector management
├── deals/                 # Offer model, forms, views, and URLs
├── pricing/               # Pricing models, configuration, and calculator
├── general/                # Home page and shared helpers
├── templates/              # Shared and app templates
│   ├── clients/
│   ├── deals/
│   ├── partials/
│   ├── pricing/
│   └── ...
├── static/
│   └── css/style.css       # Main stylesheet
├── manage.py
└── requirements.txt
```

## Requirements

-   Python compatible with the Django version pinned in
    `requirements.txt`
-   `pip`

Install the exact dependencies listed by the project:

``` bash
python -m pip install -r requirements.txt
```

## Setup and run locally

### 1. Create and activate a virtual environment

**Windows (PowerShell):**

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

``` bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Apply database migrations

``` bash
python manage.py migrate
```

If you have changed Django models and need to create new migrations,
run:

``` bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create an administrator account (optional)

``` bash
python manage.py createsuperuser
```

### 5. Start the development server

``` bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser.

## Main pages

  Area                URL
  ------------------- ------------------------
  Home             `/`
  Offers           `/deals/`
  Price calculator `/pricing/calculator/`
  Pricing setup    `/pricing/`
  Client setup     `/clients/`
  Sector setup     `/clients/sectors/`

## Initial pricing setup

Before calculating prices or creating offers, configure the required
pricing data:

1.  Create a pricing year.
2.  Create at least one channel.
3.  Create target groups and assign channels to them.
4.  Add a base price for each required target group and pricing year.
5.  Configure all 12 monthly coefficients for the pricing year.
6.  Configure index bands for both Prime Time and Channel Split.
7.  Open the price calculator and enter the required percentages.
8.  Create an offer from the offer section.

The calculator may report a validation or configuration error if
required pricing data is missing or the selected percentages are outside
the supported range.


## Configuration and production notes

The included settings are intended for local development. Before
deploying the application:

-   Set `DEBUG = False`.
-   Use a secure, environment-provided `SECRET_KEY`; do not commit
    production secrets.
-   Configure `ALLOWED_HOSTS`.
-   Configure HTTPS and appropriate security settings.
-   Consider a production database and a deployment-specific
    static-files setup.
-   Review authentication and authorization requirements for the
    intended users.

## License

No license is specified in this repository. Add a license file if you
intend to distribute the project publicly.


