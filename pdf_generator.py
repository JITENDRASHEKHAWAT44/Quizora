from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    KeepTogether,
)


# ============================================================
# PDF STYLES
# ============================================================

def get_styles():

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "QuizoraTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )

    subtitle_style = ParagraphStyle(
        "QuizoraSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=10 * mm,
    )

    question_style = ParagraphStyle(
        "Question",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
    )

    option_style = ParagraphStyle(
        "Option",
        parent=styles["Normal"],
        fontSize=10.5,
        leading=15,
        leftIndent=7 * mm,
        spaceAfter=2 * mm,
    )

    answer_style = ParagraphStyle(
        "Answer",
        parent=styles["Normal"],
        fontSize=10.5,
        leading=15,
        leftIndent=5 * mm,
        spaceBefore=2 * mm,
        spaceAfter=3 * mm,
    )

    explanation_style = ParagraphStyle(
        "Explanation",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        leftIndent=5 * mm,
        spaceAfter=4 * mm,
    )

    metadata_style = ParagraphStyle(
        "Metadata",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=12,
        textColor=colors.grey,
        spaceAfter=2 * mm,
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "question": question_style,
        "option": option_style,
        "answer": answer_style,
        "explanation": explanation_style,
        "metadata": metadata_style,
    }


# ============================================================
# SAFE TEXT
# ============================================================

def safe_text(value):
    """
    Convert values into strings safe for ReportLab.
    """

    if value is None:
        return ""

    return str(value)


def escape_text(text):
    """
    Escape characters that can be interpreted as
    ReportLab paragraph markup.
    """

    text = safe_text(text)

    text = text.replace(
        "&",
        "&amp;",
    )

    text = text.replace(
        "<",
        "&lt;",
    )

    text = text.replace(
        ">",
        "&gt;",
    )

    return text


# ============================================================
# COMMON PDF HEADER
# ============================================================

def build_header(
    story,
    title,
    quiz,
    styles,
):

    story.append(
        Paragraph(
            escape_text(title),
            styles["title"],
        )
    )

    total_questions = len(
        quiz.get(
            "questions",
            [],
        )
    )

    story.append(
        Paragraph(
            f"Total Questions: {total_questions}",
            styles["subtitle"],
        )
    )


# ============================================================
# QUESTION BLOCK
# ============================================================

def build_question_block(
    question,
    number,
    styles,
    include_answer=False,
):

    block = []

    question_text = escape_text(
        question.get(
            "question",
            "",
        )
    )

    block.append(
        Paragraph(
            f"<b>{number}. {question_text}</b>",
            styles["question"],
        )
    )

    options = question.get(
        "options",
        [],
    )

    for index, option in enumerate(
        options
    ):

        letter = chr(
            65 + index
        )

        option_text = escape_text(
            option
        )

        block.append(
            Paragraph(
                f"<b>{letter}.</b> {option_text}",
                styles["option"],
            )
        )


    # --------------------------------------------------------
    # Answer + Explanation
    # --------------------------------------------------------

    if include_answer:

        correct_answer = escape_text(
            question.get(
                "correct_answer",
                "",
            )
        )

        explanation = escape_text(
            question.get(
                "explanation",
                "",
            )
        )

        block.append(
            Paragraph(
                f"<b>Correct Answer:</b> "
                f"{correct_answer}",
                styles["answer"],
            )
        )

        block.append(
            Paragraph(
                f"<b>Explanation:</b> "
                f"{explanation}",
                styles["explanation"],
            )
        )

    return block


# ============================================================
# CREATE QUESTION PAPER
# ============================================================

def create_question_pdf(
    quiz,
    output_path,
    title="Quizora — Question Paper",
):

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    styles = get_styles()

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="Quizora",
    )

    story = []

    build_header(
        story,
        title,
        quiz,
        styles,
    )

    questions = quiz.get(
        "questions",
        [],
    )

    for number, question in enumerate(
        questions,
        start=1,
    ):

        block = build_question_block(
            question=question,
            number=number,
            styles=styles,
            include_answer=False,
        )

        story.append(
            KeepTogether(block)
        )

    document.build(
        story
    )

    return str(
        output_path
    )


# ============================================================
# CREATE ANSWER KEY
# ============================================================

def create_answer_pdf(
    quiz,
    output_path,
    title="Quizora — Answer Key",
):

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    styles = get_styles()

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="Quizora",
    )

    story = []

    build_header(
        story,
        title,
        quiz,
        styles,
    )

    questions = quiz.get(
        "questions",
        [],
    )

    for number, question in enumerate(
        questions,
        start=1,
    ):

        block = build_question_block(
            question=question,
            number=number,
            styles=styles,
            include_answer=True,
        )

        story.append(
            KeepTogether(block)
        )

    document.build(
        story
    )

    return str(
        output_path
    )


# ============================================================
# TEST MODE
# ============================================================

if __name__ == "__main__":

    input_file = Path(
        "output/quiz.json"
    )

    if not input_file.exists():

        raise FileNotFoundError(
            "output/quiz.json not found."
        )

    import json

    with open(
        input_file,
        "r",
        encoding="utf-8",
    ) as file:

        quiz = json.load(file)


    question_pdf = create_question_pdf(
        quiz=quiz,
        output_path="output/questions.pdf",
    )

    answer_pdf = create_answer_pdf(
        quiz=quiz,
        output_path="output/answer_key.pdf",
    )

    print(
        "\nPDF generation completed."
    )

    print(
        f"Question paper: {question_pdf}"
    )

    print(
        f"Answer key: {answer_pdf}"
    )