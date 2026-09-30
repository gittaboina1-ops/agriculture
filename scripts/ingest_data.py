import os
import json
import pandas as pd
from typing import Dict, Any, List

def ingest_structured_csv(file_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    df = pd.read_csv(file_path)
    return df.to_dict(orient="records")

def ingest_unstructured_text(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Simple rule-based agricultural entity recognition
    found_entities = []
    for term in ["Tomato", "Early Blight", "Alternaria solani", "Copper Hydroxide", "Neem Oil", "Humidity"]:
        if term.lower() in content.lower():
            found_entities.append(term)

    return {
        "filename": os.path.basename(file_path),
        "char_count": len(content),
        "entities_identified": found_entities,
        "content_excerpt": content[:300]
    }

if __name__ == "__main__":
    print("Ingesting structured datasets...")
    crops = ingest_structured_csv("data/crops.csv")
    print(f"Ingested {len(crops)} crops.")
    
    print("\nIngesting unstructured research documents...")
    doc1 = ingest_unstructured_text("data/documents/DOC_001_early_blight_epidemiology.txt")
    print(f"Ingested: {doc1['filename']} - Found entities: {doc1['entities_identified']}")
    doc4 = ingest_unstructured_text("data/documents/DOC_004_botanical_fungicides_meta_analysis.txt")
    print(f"Ingested: {doc4['filename']} - Found entities: {doc4['entities_identified']}")
