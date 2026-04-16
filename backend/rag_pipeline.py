from embeddings import get_embedding

# =========================
# MAIN RAG FUNCTION
# =========================
def answer_question(question, vector_store, client, username=None):

    # STEP 1: create query embedding
    query_emb = get_embedding(question, client)

    # STEP 2: retrieve relevant chunks (filtered by username)
    relevant_chunks = vector_store.search(query_emb, k=3, username=username)

    # STEP 3: safety check
    if not relevant_chunks:
        return "I don't have enough information in the uploaded documents yet. Please upload a PDF first."

    # STEP 4: build context
    context = "\n\n".join(relevant_chunks)

    # STEP 5: LLM call
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful AI customer support assistant. "
                    "Answer ONLY using the provided context. "
                    "If the context does not contain the answer, say I don't have enough information in the uploaded documents yet. Please upload a PDF first."
                )
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ]
    )

    return response.choices[0].message.content
