import streamlit as st
import openai
import pinecone
import os
from dotenv import load_dotenv

load_dotenv()

# Load API keys from environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')
pc = pinecone.Pinecone(api_key = os.environ["PINECONE_API_KEY"])

# Initialize Pinecone index
index_name = 'class-objective-all'  # Replace with your Pinecone index name
index = pc.Index(index_name)

# Function to classify objective using GPT-4
def classify_objective_gpt4(objective: str):
    if not objective or len(objective) < 5:
        return "Invalid input. Please provide a meaningful objective."

    # Step 1: Get Embeddings for the input
    response = openai.Embedding.create(
        input=objective.strip().lower(),
        model="text-embedding-ada-002"
    )
    query_embedding = response["data"][0]["embedding"]

    # Step 2: Query Pinecone for top 5 matches
    results = index.query(vector=query_embedding, top_k=5, include_metadata=True)

    if not results["matches"]:
        return "No suitable class found."

    # Step 3: Prepare context for GPT-4
    matched_classes = [
        f"Class {m['id']}: {m['metadata']['description']}"
        for m in results["matches"]
    ]
    context = "\n".join(matched_classes)

    # Step 4: Use GPT-4 to determine the best class
    prompt = f"""
    You are an expert in trademark classification. Given the following objective:

    "{objective}"

    And these possible trademark classes:
    {context}

    """

    gpt_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a trademark classification assistant."},
                  {"role": "user", "content": prompt}]
    )

    return gpt_response["choices"][0]["message"]["content"]

# Streamlit App
def main():
    st.title("Trademark Classification Assistant")
    st.write("Enter an objective to classify it into a trademark class.")

    # Text input for objective
    objective = st.text_area("Enter Objective", "", height=150)

    if st.button("Classify"):
        if objective:
            # Call the function to classify the objective
            result = classify_objective_gpt4(objective)
            st.subheader("Classification Result:")
            st.write(result)
        else:
            st.warning("Please enter an objective.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
