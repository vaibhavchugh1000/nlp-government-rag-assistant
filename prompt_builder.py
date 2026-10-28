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

        evidence_id = document.get(
           "evidence_id",
            f"E{index:03d}"
        )

        context_parts.append(
           f"[Evidence ID: {evidence_id}]\n"
           f"[Source: {source}]\n"
           f"[Chunk ID: {document.get('chunk_id', 'Unknown')}]\n"
           f"{text}"
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
   Answer the user's question first in 2–3 concise sentences.
   Summarize the main conclusion without repeating the
   individual points that will appear under Key Findings.

2. Key Findings:
   Present the main findings from the provided government
   document context as clear bullet points.

Use only information supported by the provided context.
Do not invent facts or make unsupported predictions.

If the context does not contain enough information,
clearly state this limitation.

Citation rules:
- Each Key Finding must include the Evidence ID or IDs
  that directly support that specific finding.
- Examine all provided evidence chunks before selecting citations.
- Do not automatically reuse E001 or any other ID for every finding.
- Different findings may cite the same Evidence ID only when
  that evidence genuinely supports each finding.
- Use multiple Evidence IDs when multiple chunks jointly
  support a finding.
- Use only Evidence IDs explicitly provided in the context.
- Never invent, modify, or guess an Evidence ID.
- If no retrieved evidence supports a claim, do not present
  that claim as an established fact.
- Preserve the exact citation format, such as [E001] or [E003].
"""

    return prompt.strip()