# PLN Recruitment Intelligence Demo

Streamlit dashboard for the HCTA recruitment demo. It includes:

- End-to-end applicant-to-contract funnel
- Pipeline duration, SLA, and bottleneck analysis
- Recruitment-method comparison
- Vacancy fulfilment and geographic distribution
- Planned-versus-actual placement alignment
- Candidate–position matching
- Basic recruitment chatbot with an optional OpenAI-compatible LLM

## 1. Setup

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Optional chatbot credentials

The predefined chatbot questions work without API credentials.

For more flexible questions, copy:

```text
.streamlit/secrets.toml.example
```

to:

```text
.streamlit/secrets.toml
```

Then replace the placeholder values with your OpenAI-compatible endpoint, API key, and model.

## 3. Run

```bash
streamlit run app.py
```

## Data notes

- The project uses synthetic demo extensions for vacancy, contract, placement, and pipeline history.
- Candidate PII is not displayed on the dashboard.
- Candidate matching does not use gender, religion, marital status, name, address, or identity numbers.
- The current project reads CSV files with Pandas and caches the prepared data in Streamlit.
