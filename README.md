<div align="center">

# 🎓 Quizora

**Turn any study PDF into a graded quiz — questions, difficulty mix, and answer key, all in one click.**

[![Made with Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)

**🔗 [Live Demo](https://quizora.streamlit.app/)**  &nbsp;·&nbsp; [Report a Bug](../../issues) &nbsp;·&nbsp; [Request a Feature](../../issues)

</div>

---

## ✨ What is Quizora?

Studying from a PDF is slow. Quizora reads the material for you and hands back a real quiz — multiple-choice questions, a controlled Easy/Medium/Hard split, and a full answer key with explanations — ready to print, share, or drop into an LMS.

Upload a chapter, set your difficulty mix, and get a quiz in the time it takes to make coffee.

<div align="center">
<!-- Replace with an actual screenshot or GIF once deployed -->
<img src="https://via.placeholder.com/900x500?text=Quizora+Screenshot" alt="Quizora screenshot" width="850">
</div>

## 🚀 Features

| | |
|---|---|
| 📎 **Any PDF, in** | Lecture notes, textbook chapters, study guides — just drag and drop |
| 🎚️ **Tunable difficulty** | Set Easy / Medium / Hard percentages, previewed live before you generate |
| 🤖 **AI-generated questions** | Multiple-choice questions with correct answers and explanations, grounded in your material |
| 📄 **Export-ready output** | Printable question paper (PDF), answer key with explanations (PDF), and raw data (JSON) |
| 👀 **Instant preview** | Review every question, topic, and difficulty badge before you download anything |
| ⚡ **Zero setup for end users** | One page, one upload, one button — no accounts, no config |

## 🖥️ Live Demo

Try it now: **[quizora.streamlit.app](https://quizora.streamlit.app/)**

> No installation needed — upload a PDF and generate a quiz directly in your browser.

## 🛠️ Tech Stack

- **[Streamlit](https://streamlit.io/)** — interactive web UI
- **[LlamaIndex](https://www.llamaindex.ai/)** — PDF parsing, indexing, and retrieval that grounds each generated question in the source material
- **`pipeline.py`** — PDF ingestion & AI-driven quiz generation
- **`pdf_generator.py`** — question paper & answer key PDF export

## 📦 Getting Started

### Prerequisites

- Python 3.9+
- An API key for the LLM provider used in `pipeline.py`

### Installation

```bash
git clone https://github.com/<your-username>/quizora.git
cd quizora
pip install -r requirements.txt
```

### Configuration

Create `.streamlit/secrets.toml`:

```toml
API_KEY = "your-api-key-here"
```

### Run locally

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## 📖 Usage

1. Set the number of questions and the Easy/Medium/Hard split in the sidebar
2. Upload a study PDF
3. Click **Generate Quiz**
4. Download the question paper, answer key, or raw JSON — or scroll through the in-app preview

## 📁 Project Structure

```
quizora/
├── app.py              # Streamlit UI
├── pipeline.py          # PDF ingestion + quiz generation logic
├── pdf_generator.py     # Question paper & answer key PDF export
├── requirements.txt
└── .streamlit/
    └── secrets.toml      # API keys (gitignored)
```

## 🗺️ Roadmap

- [ ] Support for DOCX / PPTX study material
- [ ] Adjustable question types (true/false, short answer)
- [ ] Shareable quiz links
- [ ] Export to Google Forms / Kahoot

## 🤝 Contributing

Contributions, issues, and feature requests are welcome — check the [issues page](../../issues).

1. Fork the repo
2. Create your branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push and open a PR

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

---

<div align="center">
Made with 🎓 by <a href="https://github.com/<your-username>">your name</a>
</div>
