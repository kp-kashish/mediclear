# MediClear

**Upload your blood test. Understand it in seconds.**

MediClear is an open-source, privacy-first AI agent that reads medical lab report PDFs, explains results in plain language, generates questions to ask your doctor, and tracks biomarker trends over time.

---

## Features

- PDF upload with encrypted S3 storage (24h auto-delete)
- Structured biomarker extraction via AWS Textract
- Plain-language explanations powered by LangGraph agent
- Traffic-light scoring (normal / borderline / abnormal)
- Questions to ask your doctor generated from abnormal values
- Biomarker trend tracking across multiple reports
- Multilingual output: English, German, Hindi
- Confidence scoring on uncertain extractions

---

## License

MIT