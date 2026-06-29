# N26 Case Study

## Live app

**[https://n26case-korcankomili.streamlit.app/](https://n26case-korcankomili.streamlit.app/)**

Interactive funnel dashboard. Date range filter, channel and country breakdowns, step-level conversion table.

---

## What's in here

| Path | What it is |
|------|------------|
| `solutions/task1.ipynb` | Funnel analysis and channel effectiveness. Data quality, step-level conversion rates, statistical testing across channels and countries. The main finding: the dataset is intentionally flat, and I explain why that changes every answer. |
| `solutions/task2.ipynb` | A/B test: Metal vs Standard creative on paid social. Experiment integrity checks, metric design, chi-square tests, residual analysis, and what I'd fix before running this again. |
| `solutions/task3.ipynb` | Stakeholder takeaways. What the data can and can't tell us, across channel efficiency, the campaign experiment, and attribution. No numbers, just the business implications. |
| `app.py` | Streamlit dashboard source. |
| `src/` | Shared modules for data cleaning, charts, and statistical tests. Used across all three notebooks. |
| `data/` | Raw datasets. `part_a_dataset.csv` is the funnel data. `part_b_dataset.csv` is the A/B experiment. |

---

## Running locally

```bash
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

App runs at `http://localhost:8501`.
