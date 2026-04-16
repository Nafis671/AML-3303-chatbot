from openai import OpenAI

def get_embedding(text, client):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

