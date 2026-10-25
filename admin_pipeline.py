from pathlib import Path
from pdf_loader import load_pdf
from docx_loader import load_docx
from txt_loader import load_txt
from cleaner import clean_records
from chunker import chunk_records
from embedding_model import create_embeddings
from vector_store import add_documents
from vector_store import collection

def process_document(document_path):
    
    extension=Path(document_path).suffix.lower()
    
    document_id=Path(document_path).stem
    
    existing=collection.get(where={
        "document_id" : document_id
    },limit=1)
    
    if existing["ids"]:
        
        print("document already exists in the vector_db")
        
        return {
            
           "status" : "skipped",
            "document_name": Path(document_path).name,
            "chunks_created": 0,
            "message": "document already exists in the vector database",
            "success": False
        }
    if extension==".pdf" : 
        records=load_pdf(document_path)
    elif extension==".txt" : 
        records=load_txt(document_path)
    elif extension==".docx":
        records=load_docx(document_path)
        
    else : 
        raise ValueError("invalid extension")
    
    cleaned_records=clean_records(records)
    
    chunks=chunk_records(cleaned_records)
    
    texts=[chunk["text"] for chunk in chunks]
    
    embeddings=create_embeddings(texts)
    
    add_documents(chunks,embeddings)
    
    print("document processed and stored in vector db successfully")
     
    return {
        "document_name": Path(document_path).name,
        "chunks_created": len(chunks),
        "success": True
    }
