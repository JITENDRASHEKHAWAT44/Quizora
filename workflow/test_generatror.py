from generator import generate_mcqs


context = """
Decision trees are supervised machine learning algorithms used for
classification and regression.

A decision tree consists of nodes and branches. The root node represents
the starting point. Internal nodes represent decisions based on features,
and leaf nodes represent the final prediction.

Entropy is a measure of impurity in a dataset. Lower entropy means the
dataset is more pure, while higher entropy means greater impurity.
"""


result = generate_mcqs(
    context=context,
    number_of_questions=5
)


for i, mcq in enumerate(result.questions, start=1):
    print(f"\nQuestion {i}:")
    print(mcq.question)

    for j, option in enumerate(mcq.options):
        print(f"{chr(65 + j)}. {option}")

    print(f"Correct Answer: {mcq.correct_answer}")
    print(f"Explanation: {mcq.explanation}")