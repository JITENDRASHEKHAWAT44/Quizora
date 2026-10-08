import json
from collections import Counter
from pathlib import Path

import streamlit as st

from pipeline import generate_quiz_pipeline
from pdf_generator import create_answer_pdf, create_question_pdf

# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Quizora",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

DIFFICULTY_STYLE = {
    "easy": ("Easy", "#059669", "#D1FAE5"),
    "medium": ("Medium", "#D97706", "#FEF3C7"),
    "hard": ("Hard", "#DC2626", "#FEE2E2"),
}


def inject_styles() -> None:
    st.markdown(
        """
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1100px; }
    .quizora-hero {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 55%, #6366F1 100%);
        border-radius: 16px;
        padding: 2rem 2.25rem;
        margin-bottom: 1.75rem;
        color: #fff;
        box-shadow: 0 12px 40px rgba(79, 70, 229, 0.25);
    }
    .quizora-hero h1 { color: #fff !important; font-size: 2rem !important; margin: 0 0 0.35rem 0 !important; }
    .quizora-hero p { color: rgba(255,255,255,0.92); margin: 0; font-size: 1.05rem; line-height: 1.5; }
    .quizora-badge {
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.35rem;
        vertical-align: middle;
    }
    .quizora-card {
        background: #fff;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.25rem 1.35rem;
        margin-bottom: 0.75rem;
    }
    div[data-testid="stSidebar"] { background: #F1F5F9; }
    div[data-testid="stSidebar"] .block-container { padding-top: 1.25rem; }
    .upload-hint { color: #64748B; font-size: 0.9rem; margin-top: 0.25rem; }
</style>
""",
        unsafe_allow_html=True,
    )


def difficulty_badge(level: str) -> str:
    key = (level or "medium").lower()
    label, fg, bg = DIFFICULTY_STYLE.get(key, DIFFICULTY_STYLE["medium"])
    return (
        f'<span class="quizora-badge" style="background:{bg};color:{fg};">'
        f"{label}</span>"
    )


def topic_badge(topic: str) -> str:
    text = topic or "General"
    return (
        f'<span class="quizora-badge" style="background:#EEF2FF;color:#4338CA;">'
        f"{text}</span>"
    )


def init_session_state() -> None:
    defaults = {
        "quiz_result": None,
        "question_pdf": None,
        "answer_pdf": None,
        "json_file": None,
        "gen_meta": None,
        "practice_answers": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_hero() -> None:
    st.markdown(
        """
<div class="quizora-hero">
  <h1>Quizora</h1>
  <p>Turn any study PDF into source-grounded multiple-choice questions —
  with a tuned difficulty mix, printable PDFs, and an instant preview.</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[int, int, int, int]:
    with st.sidebar:
        st.markdown("### Quiz settings")
        number_of_questions = st.number_input(
            "Number of questions",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
            help="How many MCQs to generate from the document.",
        )

        st.divider()
        st.markdown("**Difficulty mix**")
        st.caption("Percentages must add up to 100%.")

        easy_percent = st.slider("Easy", 0, 100, 30)
        medium_percent = st.slider("Medium", 0, 100, 50)
        hard_percent = st.slider("Hard", 0, 100, 20)
        total_percent = easy_percent + medium_percent + hard_percent

        if total_percent != 100:
            st.warning(f"Total is {total_percent}% — adjust to reach 100%.")
        else:
            st.success("Distribution: 100%")

        st.divider()
        st.markdown("**Pipeline**")
        st.caption(
            "Ingest → analyze topics → plan → retrieve → generate → validate"
        )

    return number_of_questions, easy_percent, medium_percent, hard_percent


def run_generation(
    uploaded_file,
    pdf_path: Path,
    number_of_questions: int,
    easy_percent: int,
    medium_percent: int,
    hard_percent: int,
) -> None:
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    status = st.status("Processing your document…", expanded=True)

    try:
        status.write("Reading and indexing PDF…")
        status.write("Analyzing topics…")
        status.write("Planning question slots…")
        status.write("Retrieving source context…")
        status.write("Generating MCQs…")
        status.write("Running structural and semantic validation…")

        result = generate_quiz_pipeline(
            pdf_path=str(pdf_path),
            number_of_questions=number_of_questions,
            easy_percent=easy_percent,
            medium_percent=medium_percent,
            hard_percent=hard_percent,
        )

        status.write("Building PDF exports…")

        json_path = output_dir / "quiz.json"
        question_pdf_path = output_dir / "question_paper.pdf"
        answer_pdf_path = output_dir / "answer_key.pdf"

        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=4, ensure_ascii=False)

        create_question_pdf(quiz=result, output_path=str(question_pdf_path))
        create_answer_pdf(quiz=result, output_path=str(answer_pdf_path))

        status.update(label="Quiz ready", state="complete", expanded=False)

        st.session_state.quiz_result = result
        st.session_state.question_pdf = str(question_pdf_path)
        st.session_state.answer_pdf = str(answer_pdf_path)
        st.session_state.json_file = str(json_path)
        st.session_state.practice_answers = {}
        st.session_state.gen_meta = {
            "requested": number_of_questions,
            "pdf_name": uploaded_file.name,
            "easy": easy_percent,
            "medium": medium_percent,
            "hard": hard_percent,
        }
        st.toast("Quiz generated successfully.", icon="✅")

    except Exception as exc:
        status.update(label="Generation failed", state="error", expanded=True)
        st.error(f"Something went wrong: {exc}")


def render_upload_section(
    total_percent: int,
    number_of_questions: int,
    easy_percent: int,
    medium_percent: int,
    hard_percent: int,
) -> None:
    st.markdown("#### Upload study material")
    st.markdown(
        '<p class="upload-hint">PDF lecture notes, textbook chapters, or study guides.</p>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choose a PDF",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.success(f"**{uploaded_file.name}** · {uploaded_file.size / 1024:.1f} KB")

    col_gen, col_clear = st.columns([3, 1])
    with col_gen:
        generate_clicked = st.button(
            "Generate quiz",
            type="primary",
            use_container_width=True,
            disabled=total_percent != 100,
        )
    with col_clear:
        if st.button("Clear results", use_container_width=True):
            st.session_state.quiz_result = None
            st.session_state.practice_answers = {}
            st.rerun()

    if generate_clicked:
        if uploaded_file is None:
            st.error("Upload a PDF before generating.")
            return
        if total_percent != 100:
            st.error("Set Easy + Medium + Hard to 100%.")
            return

        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        pdf_path = data_dir / uploaded_file.name
        with open(pdf_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        run_generation(
            uploaded_file,
            pdf_path,
            number_of_questions,
            easy_percent,
            medium_percent,
            hard_percent,
        )


def render_overview(quiz: dict) -> None:
    questions = quiz.get("questions", [])
    meta = st.session_state.gen_meta or {}
    requested = meta.get("requested", len(questions))
    pdf_name = meta.get("pdf_name", "—")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Requested", requested)
    c2.metric("Generated", len(questions))
    c3.metric("Source", pdf_name[:24] + ("…" if len(pdf_name) > 24 else ""))
    c4.metric("Status", "Ready")

    if not questions:
        st.info("No questions in this quiz.")
        return

    diff_counts = Counter(
        (q.get("difficulty") or "medium").lower() for q in questions
    )
    topic_counts = Counter(q.get("topic") or "General" for q in questions)

    st.markdown("##### Breakdown")
    left, right = st.columns(2)
    with left:
        st.caption("By difficulty")
        chart_data = {
            DIFFICULTY_STYLE.get(k, DIFFICULTY_STYLE["medium"])[0]: v
            for k, v in sorted(diff_counts.items())
        }
        st.bar_chart(chart_data, height=180)
    with right:
        st.caption("Top topics")
        for topic, count in topic_counts.most_common(5):
            st.write(f"**{topic}** — {count} question{'s' if count != 1 else ''}")

    st.markdown("##### Downloads")
    d1, d2, d3 = st.columns(3)
    paths = (
        ("question_pdf", "Question paper", "question_paper.pdf", "application/pdf"),
        ("answer_pdf", "Answer key", "answer_key.pdf", "application/pdf"),
        ("json_file", "JSON data", "quiz.json", "application/json"),
    )
    for col, (state_key, label, fname, mime) in zip((d1, d2, d3), paths):
        path = st.session_state.get(state_key)
        if path and Path(path).exists():
            with col:
                with open(path, "rb") as file:
                    st.download_button(
                        label,
                        file,
                        file_name=fname,
                        mime=mime,
                        use_container_width=True,
                    )


def render_preview(quiz: dict, show_answers: bool) -> None:
    questions = quiz.get("questions", [])
    if not questions:
        return

    for q in questions:
        qid = q.get("question_id", "")
        header = f"Question {qid}"
        badges = topic_badge(q.get("topic", "")) + difficulty_badge(
            q.get("difficulty", "")
        )
        st.markdown(
            f'<div class="quizora-card"><strong>{header}</strong> {badges}</div>',
            unsafe_allow_html=True,
        )
        st.write(q.get("question", ""))

        options = q.get("options", [])
        for idx, option in enumerate(options):
            letter = chr(65 + idx)
            st.markdown(f"**{letter}.** {option}")

        if show_answers:
            st.success(f"**Answer:** {q.get('correct_answer', '')}")
            with st.expander("Explanation"):
                st.write(q.get("explanation", ""))
            sources = q.get("sources") or []
            if sources:
                pages = sorted({str(s.get("page", "")) for s in sources if s.get("page")})
                if pages:
                    st.caption(f"Source pages: {', '.join(pages)}")

        st.divider()


def render_practice(quiz: dict) -> None:
    questions = quiz.get("questions", [])
    if not questions:
        return

    st.caption("Pick an option for each question, then check your score.")

    for q in questions:
        qid = str(q.get("question_id", ""))
        options = q.get("options", [])
        if len(options) < 4:
            continue

        labels = [f"{chr(65 + i)}. {opt}" for i, opt in enumerate(options)]
        key = f"practice_{qid}"
        choice = st.radio(
            f"**Q{qid}.** {q.get('question', '')}",
            ["(select an answer)"] + labels,
            key=key,
        )
        if choice != "(select an answer)":
            st.session_state.practice_answers[qid] = choice.split(". ", 1)[-1]

    if st.button("Score my answers", type="primary"):
        correct = 0
        for q in questions:
            qid = str(q.get("question_id", ""))
            picked = st.session_state.practice_answers.get(qid)
            if picked and picked == q.get("correct_answer"):
                correct += 1
        total = len(questions)
        pct = round(100 * correct / total) if total else 0
        st.balloons()
        st.success(f"You got **{correct} / {total}** ({pct}%).")

        with st.expander("Review answers"):
            for q in questions:
                qid = q.get("question_id", "")
                st.markdown(
                    f"**Q{qid}** — Correct: *{q.get('correct_answer', '')}*"
                )


# ============================================================
# MAIN
# ============================================================

init_session_state()
inject_styles()
render_hero()

number_of_questions, easy_percent, medium_percent, hard_percent = render_sidebar()
total_percent = easy_percent + medium_percent + hard_percent

quiz = st.session_state.quiz_result

if quiz:
    tab_overview, tab_preview, tab_practice, tab_new = st.tabs(
        ["Overview", "Preview", "Practice", "New quiz"]
    )

    with tab_overview:
        render_overview(quiz)

    with tab_preview:
        show_answers = st.toggle("Show answers and explanations", value=False)
        render_preview(quiz, show_answers)

    with tab_practice:
        render_practice(quiz)

    with tab_new:
        render_upload_section(
            total_percent,
            number_of_questions,
            easy_percent,
            medium_percent,
            hard_percent,
        )
else:
    render_upload_section(
        total_percent,
        number_of_questions,
        easy_percent,
        medium_percent,
        hard_percent,
    )
