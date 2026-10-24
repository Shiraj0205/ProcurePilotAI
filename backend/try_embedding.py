"""Quick check of the embedding model: score sample answers against a question
using cosine similarity. Run from the backend folder: python try_embedding.py
"""

import math
from rag.embeddings import get_embedding_model


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


question = "What is the approval process for purchase orders above $10,000?"

answers = [
    "Purchase orders exceeding $10,000 must be approved by the department head and the finance manager before being sent to the vendor.",
    "Vendors are paid within 30 days of receiving a valid invoice.",
    "The office cafeteria serves lunch from 12 PM to 2 PM on weekdays.",
]


def main() -> None:
    """Main function to compute and print cosine similarity scores for sample answers against a question."""
    model = get_embedding_model()

    question_vector = model.embed_query(question)
    answer_vectors = model.embed_documents(answers)

    print(f"Question: {question}\n")
    scores = [cosine_similarity(question_vector, vec) for vec in answer_vectors]
    for score, answer in sorted(zip(scores, answers), reverse=True):
        print(f"{score:.4f}  {answer}")


if __name__ == "__main__":
    main()
