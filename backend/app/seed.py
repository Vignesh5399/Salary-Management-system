"""Seed the database with a realistic organisation of 10,000 employees.

Deterministic: a fixed RNG seed means the same dataset every run, so a demo
looks the same twice and a bug found in seeded data can be reproduced.

    python -m app.seed
"""

import asyncio
import random
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.domain.compensation import ChangeReason, CompensationHistory
from app.domain.money import Money
from app.persistence.database import connect
from app.persistence.documents import compensation_to_documents
from app.persistence.models import Band, CompensationEntry, Employee, Rate

SEED = 42
HEADCOUNT = 10_000
TODAY = date(2026, 1, 1)

# (country, currency, share of headcount, band midpoint for L1 in local currency)
COUNTRIES = [
    ("IN", "INR", 0.45, Decimal("900000")),
    ("US", "USD", 0.25, Decimal("95000")),
    ("GB", "GBP", 0.15, Decimal("52000")),
    ("SG", "SGD", 0.10, Decimal("78000")),
    ("AU", "AUD", 0.05, Decimal("88000")),
]
LEVELS = ["L1", "L2", "L3", "L4", "L5", "L6"]
LEVEL_MULTIPLIER = {"L1": 1.0, "L2": 1.4, "L3": 1.9, "L4": 2.6, "L5": 3.5, "L6": 4.8}
DEPARTMENTS = [
    "Engineering",
    "Product",
    "Design",
    "Sales",
    "Marketing",
    "Finance",
    "People",
    "Support",
]
TITLES = {
    "L1": "Associate",
    "L2": "Analyst",
    "L3": "Specialist",
    "L4": "Senior Specialist",
    "L5": "Lead",
    "L6": "Principal",
}
RATES_TO_USD = {
    "INR": "0.0120",
    "USD": "1.0000",
    "GBP": "1.2700",
    "SGD": "0.7400",
    "AUD": "0.6600",
}

FIRST_NAMES = "Priya Arjun Meera Rahul Ananya Vikram Sofia James Chloe Daniel Wei Hana Omar Lucia Noah Ava Ethan Isla Kabir Divya".split()
LAST_NAMES = "Sharma Nair Iyer Patel Menon Reddy Smith Jones Taylor Brown Lim Tan Chen Garcia Rossi Dubois Okafor Novak Ahmed Silva".split()


def _band_bounds(country_midpoint: Decimal, level: str) -> tuple[Decimal, Decimal, Decimal]:
    midpoint = (country_midpoint * Decimal(str(LEVEL_MULTIPLIER[level]))).quantize(Decimal("1"))
    return midpoint * Decimal("0.80"), midpoint, midpoint * Decimal("1.20")


def _bands() -> list[Band]:
    bands = []
    for country, currency, _, base in COUNTRIES:
        for level in LEVELS:
            low, mid, high = _band_bounds(base, level)
            bands.append(
                Band(
                    level=level,
                    country=country,
                    currency=currency,
                    minimum_minor=Money.of(f"{low:.2f}", currency).amount_minor,
                    midpoint_minor=Money.of(f"{mid:.2f}", currency).amount_minor,
                    maximum_minor=Money.of(f"{high:.2f}", currency).amount_minor,
                )
            )
    return bands


def _rates() -> list[Rate]:
    start = datetime(2018, 1, 1, tzinfo=UTC)
    return [
        Rate(base=currency, quote="USD", rate=rate, effective_from=start)
        for currency, rate in RATES_TO_USD.items()
        if currency != "USD"
    ]


def _employee(number: int, rng: random.Random) -> Employee:
    country, currency, _, base = rng.choices(
        COUNTRIES, weights=[share for *_, share, _ in COUNTRIES]
    )[0]
    level = rng.choices(LEVELS, weights=[30, 25, 20, 13, 8, 4])[0]
    _, midpoint, _ = _band_bounds(base, level)

    # Most people sit near the midpoint; a few sit well outside it, which is
    # what the exceptions view exists to surface.
    spread = rng.gauss(1.0, 0.11)
    if rng.random() < 0.02:
        spread = rng.choice([rng.uniform(0.68, 0.78), rng.uniform(1.22, 1.35)])
    starting = (midpoint * Decimal(str(round(spread, 4))) * Decimal("0.85")).quantize(
        Decimal("1")
    )

    hired = TODAY - timedelta(days=rng.randint(120, 2900))
    history = CompensationHistory.starting_with(
        Money.of(f"{starting:.2f}", currency), on=hired
    )

    # An annual review each April the employee was present for.
    for year in range(hired.year + 1, TODAY.year):
        review = date(year, 4, 1)
        if review <= hired or rng.random() < 0.15:
            continue
        promoted = rng.random() < 0.12
        history = history.raise_by(
            Decimal(str(round(rng.uniform(12, 20) if promoted else rng.uniform(3, 9), 2))),
            effective_from=review,
            reason=ChangeReason.PROMOTION if promoted else ChangeReason.MERIT,
        )

    name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    return Employee(
        employee_no=f"ACM-{number:05d}",
        name=name,
        email=f"{name.lower().replace(' ', '.')}.{number}@acme.example",
        country=country,
        department=rng.choice(DEPARTMENTS),
        level=level,
        job_title=TITLES[level],
        hire_date=datetime(hired.year, hired.month, hired.day, tzinfo=UTC),
        status="active",
        compensation=[
            CompensationEntry(**document) for document in compensation_to_documents(history)
        ],
        current_amount_minor=history.current.amount_minor,
        current_currency=history.current.currency.code,
    )


async def seed() -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    await connect(client, settings.database_name)

    for model in (Employee, Band, Rate):
        await model.get_motor_collection().drop()
    await connect(client, settings.database_name)  # recreate the indexes

    await Band.insert_many(_bands())
    await Rate.insert_many(_rates())

    rng = random.Random(SEED)
    batch: list[Employee] = []
    for number in range(1, HEADCOUNT + 1):
        batch.append(_employee(number, rng))
        if len(batch) == 1_000:
            await Employee.insert_many(batch)
            print(f"  {number:,} employees")
            batch = []
    if batch:
        await Employee.insert_many(batch)

    print(f"Seeded {HEADCOUNT:,} employees, {len(_bands())} bands, {len(_rates())} rates.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
