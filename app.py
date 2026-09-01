import json
from pathlib import Path

import streamlit as st

from pipeline import generate_quiz_pipeline
from pdf_generator import (
    create_question_pdf,
    create_answer_pdf,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Quizora",
    page_icon="📝",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title("📝 Quizora")

st.markdown(
    """
### AI-Powered RAG Quiz Generator

Upload your study material and generate
source-grounded MCQs with answers and explanations.
"""
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Quiz Settings")

    # ----------------------------------------
    # Number of questions
    # ----------------------------------------

    number_of_questions = st.number_input(
        "Number of Questions",
        min_value=1,
        max_value=100,
        value=10,
        step=1,
    )

    st.divider()

    # ----------------------------------------
    # Difficulty distribution
    # ----------------------------------------

    st.subheader("Difficulty Distribution")

    easy_percent = st.slider(
        "Easy (%)",
        min_value=0,
        max_value=100,
        value=30,
    )

    medium_percent = st.slider(
        "Medium (%)",
        min_value=0,
        max_value=100,
        value=50,
    )

    hard_percent = st.slider(
        "Hard (%)",
        min_value=0,
        max_value=100,
        value=20,
    )

    total_percent = (
        easy_percent
        + medium_percent
        + hard_percent
    )

    if total_percent != 100:

        st.warning(
            f"Difficulty percentages total "
            f"{total_percent}%. They must equal 100%."
        )

    else:

        st.success(
            "Difficulty distribution: 100%"
        )


# ============================================================
# PDF UPLOAD
# ============================================================

st.subheader("📄 Upload Study Material")

uploaded_file = st.file_uploader(
    "Upload a PDF",
    type=["pdf"],
)


if uploaded_file:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    st.caption(
        f"Size: "
        f"{uploaded_file.size / 1024:.1f} KB"
    )


# ============================================================
# GENERATE BUTTON
# ============================================================

generate_button = st.button(
    "🚀 Generate Quiz",
    type="primary",
    use_container_width=True,
)


# ============================================================
# GENERATION
# ============================================================

if generate_button:

    # ----------------------------------------
    # Validate PDF
    # ----------------------------------------

    if uploaded_file is None:

        st.error(
            "Please upload a PDF first."
        )

        st.stop()


    # ----------------------------------------
    # Validate difficulty
    # ----------------------------------------

    if total_percent != 100:

        st.error(
            "Easy + Medium + Hard percentages "
            "must equal 100%."
        )

        st.stop()


    # ----------------------------------------
    # Prepare directories
    # ----------------------------------------

    data_dir = Path("data")
    output_dir = Path("output")

    data_dir.mkdir(
        exist_ok=True
    )

    output_dir.mkdir(
        exist_ok=True
    )


    # ----------------------------------------
    # Save uploaded PDF
    # ----------------------------------------

    pdf_path = (
        data_dir /
        uploaded_file.name
    )

    with open(
        pdf_path,
        "wb",
    ) as file:

        file.write(
            uploaded_file.getbuffer()
        )


    # ========================================================
    # STATUS UI
    # ========================================================

    st.divider()

    st.subheader(
        "⚙️ Generating Your Quiz"
    )

    status = st.status(
        "Quizora is processing your document...",
        expanded=True,
    )


    try:

        # ------------------------------------
        # Stage 1
        # ------------------------------------

        status.write(
            "📥 Reading and indexing PDF..."
        )


        # ------------------------------------
        # Run complete pipeline
        # ------------------------------------

        status.write(
            "🧠 Analyzing document and identifying topics..."
        )

        status.write(
            "📋 Planning questions..."
        )

        status.write(
            "🔎 Retrieving relevant source context..."
        )

        status.write(
            "✨ Generating MCQs..."
        )

        status.write(
            "✅ Performing structural validation..."
        )

        status.write(
            "🔍 Performing semantic validation..."
        )

        status.write(
            "🛠️ Regenerating unsupported questions if required..."
        )


        result = generate_quiz_pipeline(

            pdf_path=str(
                pdf_path
            ),

            number_of_questions=(
                number_of_questions
            ),

            easy_percent=(
                easy_percent
            ),

            medium_percent=(
                medium_percent
            ),

            hard_percent=(
                hard_percent
            ),
        )


        status.write(
            "📄 Creating question paper..."
        )


        # ====================================================
        # SAVE FINAL JSON
        # ====================================================

        json_path = (
            output_dir /
            "quiz.json"
        )

        with open(
            json_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                indent=4,
                ensure_ascii=False,
            )


        # ====================================================
        # GENERATE PDFs
        # ====================================================

        question_pdf_path = (
            output_dir /
            "question_paper.pdf"
        )

        answer_pdf_path = (
            output_dir /
            "answer_key.pdf"
        )


        create_question_pdf(
            quiz=result,
            output_path=str(
                question_pdf_path
            ),
        )


        create_answer_pdf(
            quiz=result,
            output_path=str(
                answer_pdf_path
            ),
        )


        # ====================================================
        # COMPLETE
        # ====================================================

        status.update(
            label="Quiz generation completed!",
            state="complete",
            expanded=False,
        )


        st.session_state[
            "quiz_result"
        ] = result

        st.session_state[
            "question_pdf"
        ] = str(
            question_pdf_path
        )

        st.session_state[
            "answer_pdf"
        ] = str(
            answer_pdf_path
        )

        st.session_state[
            "json_file"
        ] = str(
            json_path
        )


    except Exception as e:

        status.update(
            label="Quiz generation failed.",
            state="error",
            expanded=True,
        )

        st.error(
            f"Error: {e}"
        )

        st.stop()


# ============================================================
# RESULTS
# ============================================================

if "quiz_result" in st.session_state:

    quiz = st.session_state[
        "quiz_result"
    ]

    questions = quiz.get(
        "questions",
        []
    )


    st.divider()

    st.header(
        "📊 Quiz Generated"
    )


    # ========================================================
    # STATISTICS
    # ========================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Requested",
            number_of_questions,
        )

    with col2:

        st.metric(
            "Generated",
            len(questions),
        )

    with col3:

        st.metric(
            "Status",
            "Ready",
        )


    # ========================================================
    # DOWNLOADS
    # ========================================================

    st.subheader(
        "📥 Download Files"
    )

    col1, col2, col3 = st.columns(3)


    with col1:

        with open(
            st.session_state[
                "question_pdf"
            ],
            "rb",
        ) as file:

            st.download_button(
                "📄 Question Paper",
                file,
                file_name="question_paper.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


    with col2:

        with open(
            st.session_state[
                "answer_pdf"
            ],
            "rb",
        ) as file:

            st.download_button(
                "✅ Answers + Explanations",
                file,
                file_name="answer_key.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


    with col3:

        with open(
            st.session_state[
                "json_file"
            ],
            "rb",
        ) as file:

            st.download_button(
                "💾 JSON",
                file,
                file_name="quiz.json",
                mime="application/json",
                use_container_width=True,
            )


    # ========================================================
    # QUESTION PREVIEW
    # ========================================================

    st.divider()

    st.header(
        "👀 Question Preview"
    )


    for question in questions:

        question_id = question.get(
            "question_id",
            "",
        )

        st.markdown(
            f"### Question {question_id}"
        )


        st.write(
            question.get(
                "question",
                "",
            )
        )


        options = question.get(
            "options",
            []
        )


        for index, option in enumerate(
            options
        ):

            letter = chr(
                65 + index
            )

            st.write(
                f"**{letter}.** {option}"
            )


        st.divider()