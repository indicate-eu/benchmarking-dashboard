# ICU Quality Dashboard (prototype)

This is a small prototype web application that visualizes aggregated quality indicator adherence for intensive care benchmarking. It uses randomly generated data and is intended to demonstrate UI and interactions.

Prerequisites
- Python 3.10+ recommended
- install dependencies:

```bash
pip install -r requirements.txt
```

Run

```bash
python app.py
# then open http://127.0.0.1:5000
```

Notes
- The app uses a `RandomDataProvider` (in `providers.py`). Replace or extend with an `OpenAPIDataProvider` later to fetch real data from the central hub.
- Date range selector in the top bar controls displayed period.
