NFL QB Pipeline

End-to-end data engineering pipeline built with a Medallion architecture (Bronze → Silver → Gold) to track and analyze Drake Maye's performance as quarterback of the New England Patriots. The pipeline ingests play-by-play data, cleans and validates it, and produces analytics-ready tables covering performance, situational efficiency, pressure response, receiver tendencies, and season progression.

---

## Architecture

nflreadpy (data source)

│

▼

Bronze layer        → raw play-by-play data, deduplicated and filtered for the target player

│

▼

Silver layer         → schema-enforced, validated, with derived features (success, redzone, etc.)

│

▼

Gold layer (7 tables) → analytics-ready tables for performance, splits, efficiency, momentum,

pressure, receivers, and season progression

│

▼

Consumption           → dashboards, analysis, or ML models

---

## Tech stack

- **Language:** Python 3.11+
- **Data processing:** [Polars](https://pola.rs/)
- **Data source:** [nflreadpy](https://github.com/nflverse/nflreadpy)
- **Database:** PostgreSQL
- **ORM / connection:** SQLAlchemy
- **Testing:** pytest

## Project structure

```
nfl_data_engine/
├── src/
│   ├── bronze/
│   │   └── bronze.py
│   ├── silver/
│   │   └── silver.py
│   ├── gold/
│   │   ├── qb_performance.py
│   │   ├── situational_splits.py
│   │   ├── efficiency_profile.py
│   │   ├── game_momentum.py
│   │   ├── pressure_performance.py
│   │   ├── receiver_profile.py
│   │   └── season_progression.py
│   ├── utils.py
│   └── models.py
├── tests/
│   ├── test_bronze.py
│   ├── test_silver.py
│   └── test_gold.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Gold layer tables

| Table | What it answers |
|---|---|
| `gold_qb_performance` | What did Maye do in each game? (yards, TDs, passer rating, completion %) |
| `gold_situational_splits` | How does he perform by down, score situation, quarter and home/away? |
| `gold_efficiency_profile` | What is his passing style — short vs deep, by field location? |
| `gold_game_momentum` | Is he improving over time? (4-game rolling averages) |
| `gold_pressure_overview` | How does he perform overall when hit, scrambling, or with a clean pocket? |
| `gold_pressure_by_down` | How does pressure response change by down? |
| `gold_pressure_by_quarter` | How does pressure response change by quarter? |
| `gold_pressure_by_opponent` | Which defenses pressured him the most? |
| `gold_pressure_air_yards` | Does he throw shorter when pressured? |
| `gold_receiver_overview` | Who are his most-targeted and most efficient receivers? |
| `gold_receiver_by_down` | Who does he target on each down? |
| `gold_receiver_by_situation` | Who does he target when winning, losing, or tied? |
| `gold_receiver_redzone` | Who does he target in the red zone? |
| `gold_season_progression` | How did his cumulative stats evolve week by week? |
Copy `.env.example` to `.env` and add your PostgreSQL connection string:

## How to run

Run each layer in order — Bronze must run before Silver, and Silver before any Gold table:

```bash
python src/bronze/bronze.py
python src/silver/silver.py
python src/gold/qb_performance.py
python src/gold/situational_splits.py
python src/gold/efficiency_profile.py
python src/gold/game_momentum.py
python src/gold/pressure_performance.py
python src/gold/receiver_profile.py
python src/gold/season_progression.py
```

Each script logs its progress and writes its output directly to PostgreSQL.

---

## Testing

The project includes unit tests covering the core business logic — passer rating calculation, official pass attempt filtering (excluding sacks, fumbles and two-point conversions), pressure type classification, and schema validation.

```bash
pytest
```

---

## Future improvements

- **Docker** — containerize the pipeline and PostgreSQL for one-command setup
- **Orchestration** — automate Bronze → Silver → Gold execution with Prefect
- **Cloud deployment** — run the pipeline on GCP (Cloud Run, Cloud SQL, Cloud Scheduler)
- **CI/CD** — run tests automatically on every push with GitHub Actions
- **Multi-player support** — extend the pipeline to track any QB or team by adjusting a single configuration constant


