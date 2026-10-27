from language_detector import detect_language

def build_prompt(query, retrieved_documents,language):
    """
    Build the prompt for the LLM using the user's query
    and the retrieved government document chunks.

    Returns:
        str: Prompt to be sent to the LLM.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if not retrieved_documents:
        raise ValueError("No retrieved documents available.")


    language_names={"en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "pa": "Punjabi",
        "ur": "Urdu",
        "or": "Odia",
        "as": "Assamese"
     }
    
    response_language=language_names.get(language,language)
    context_parts = []

    for index, document in enumerate(retrieved_documents, start=1):

        text = document["text"]
        metadata = document["metadata"]

        document_name = metadata.get(
            "document_name",
            "Unknown document"
        )

        page_number = metadata.get(
            "page_number"
        )

        paragraph_number = metadata.get(
            "paragraph_number"
        )

        if page_number is not None:

            source = (
                f"{document_name}, "
                f"Page {page_number}"
            )

        elif paragraph_number is not None:

            source = (
                f"{document_name}, "
                f"Paragraph {paragraph_number}"
            )

        else:

            source = document_name

        context_parts.append(
            f"[Source {index}: {source}]\n{text}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are a Government Document Assistant.

Answer the user's question using only the
provided government document context.

If the answer cannot be found in the provided
context, clearly say that the information was
not found in the available government documents.

Do not invent facts.

User Question:
{query}
the user's detected language is :
{response_language}

answer in :
{response_language}
Government Document Context:
{context}

Structure your response using these sections:

1. Direct Answer:
   Answer the user's question first in 2–4 concise sentences.

2. Key Findings:
   Present the main findings from the provided government
   document context as clear bullet points.

Use only information supported by the provided context.
Do not invent facts or make unsupported predictions.

If the context does not contain enough information,
clearly state this limitation.
"""

    return prompt.strip()