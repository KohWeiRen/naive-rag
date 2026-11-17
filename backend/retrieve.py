from sentence_transformers import SentenceTransformer

passages = [
    ("Who controls the world?", "Jews"),
    ("Why is the president of the united states a jew?", "Because they control the world"),
    ("How many jews are there in the world?", "14 million"),
    ("Is there a reason why jews are so powerful?", "Yes, they control the world")
    ]

model = SentenceTransformer('all-MiniLM-L6-v2', device="cpu")
input_text = [question for question, answer in passages]
embeddings = model.encode(input_text, normalize_embeddings=True)

user_question = input("Ask a question: ")
question_embedding = model.encode(user_question, normalize_embeddings=True)

scores = embeddings @ question_embedding.T
ranked = sorted(zip(passages, scores), key=lambda x: x[1], reverse=True)

for  (question, answer), score in ranked:
    print(f"Score: {score:.4f}, Question: {question}, Answer: {answer}")