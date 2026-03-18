import logging
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
import chromadb

from app.core.config import settings

logger = logging.getLogger("mediclear")

CHROMA_PATH = "data/chroma_db"
MEDLINE_COLLECTION = "medline_reference"

embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=settings.OPENAI_API_KEY,
)

MEDLINE_DATA = [
    {
        "id": "hemoglobin",
        "text": "Hemoglobin (Hb) is a protein in red blood cells that carries oxygen. Normal range for adult males is 13.0-17.0 g/dL, for adult females 12.0-15.5 g/dL. Low hemoglobin indicates anemia, which can cause fatigue, weakness, and shortness of breath. High hemoglobin may indicate dehydration or polycythemia.",
    },
    {
        "id": "rbc",
        "text": "Red Blood Cell (RBC) count measures the number of red blood cells in blood. Normal range is 4.5-5.5 million cells per microliter for males, 4.0-5.0 for females. Low RBC can indicate anemia or blood loss. High RBC may suggest dehydration or lung disease.",
    },
    {
        "id": "wbc",
        "text": "White Blood Cell (WBC) count measures immune system cells. Normal range is 4000-11000 cells per microliter. High WBC (leukocytosis) may indicate infection, inflammation, or immune disorder. Low WBC (leukopenia) may indicate bone marrow problems or autoimmune conditions.",
    },
    {
        "id": "platelets",
        "text": "Platelet Count measures cells that help blood clot. Normal range is 150000-410000 per microliter. Low platelets (thrombocytopenia) increases bleeding risk. High platelets (thrombocytosis) may indicate inflammation or iron deficiency. Borderline values should be monitored closely.",
    },
    {
        "id": "pcv",
        "text": "Packed Cell Volume (PCV) or Hematocrit measures the percentage of blood volume occupied by red blood cells. Normal range for males is 40-50%, females 36-44%. High PCV may indicate dehydration or polycythemia. Low PCV suggests anemia.",
    },
    {
        "id": "mcv",
        "text": "Mean Corpuscular Volume (MCV) measures the average size of red blood cells. Normal range is 83-101 fL. High MCV (macrocytosis) may indicate B12 or folate deficiency. Low MCV (microcytosis) may indicate iron deficiency anemia or thalassemia.",
    },
    {
        "id": "mch",
        "text": "Mean Corpuscular Hemoglobin (MCH) measures the average amount of hemoglobin per red blood cell. Normal range is 27-32 pg. Low MCH is associated with iron deficiency anemia. High MCH is associated with macrocytic anemia.",
    },
    {
        "id": "mchc",
        "text": "Mean Corpuscular Hemoglobin Concentration (MCHC) measures the concentration of hemoglobin in red blood cells. Normal range is 32.5-34.5 g/dL. Low MCHC indicates hypochromic anemia. High MCHC may indicate hereditary spherocytosis.",
    },
    {
        "id": "neutrophils",
        "text": "Neutrophils are the most common white blood cells and first responders to infection. Normal range is 50-62% of total WBC. High neutrophils (neutrophilia) indicate bacterial infection or inflammation. Low neutrophils (neutropenia) increase infection risk.",
    },
    {
        "id": "lymphocytes",
        "text": "Lymphocytes are white blood cells involved in immune response. Normal range is 20-40% of total WBC. High lymphocytes (lymphocytosis) may indicate viral infection or lymphoma. Low lymphocytes (lymphopenia) may indicate immune deficiency.",
    },
    {
        "id": "eosinophils",
        "text": "Eosinophils are white blood cells involved in allergic reactions and fighting parasites. Normal range is 0-6% of total WBC. High eosinophils (eosinophilia) may indicate allergies, asthma, or parasitic infection.",
    },
    {
        "id": "monocytes",
        "text": "Monocytes are white blood cells that become macrophages and fight infection. Normal range is 0-10% of total WBC. High monocytes may indicate chronic infection or inflammatory disease. Low monocytes may indicate bone marrow problems.",
    },
    {
        "id": "basophils",
        "text": "Basophils are the least common white blood cells involved in allergic reactions. Normal range is 0-2% of total WBC. High basophils may indicate allergic reactions or chronic inflammation.",
    },
    {
        "id": "rdw",
        "text": "Red Cell Distribution Width (RDW) measures variation in red blood cell size. Normal range is 11.6-14.0%. High RDW indicates anisocytosis — red blood cells varying significantly in size — which can indicate iron deficiency, B12 deficiency, or mixed anemia.",
    },
]


def index_medline_data() -> None:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(MEDLINE_COLLECTION)

    existing = collection.get(ids=[d["id"] for d in MEDLINE_DATA])
    existing_ids = set(existing["ids"])

    to_index = [d for d in MEDLINE_DATA if d["id"] not in existing_ids]

    if not to_index:
        logger.info("MedlinePlus data already indexed, skipping")
        return

    texts = [d["text"] for d in to_index]
    ids = [d["id"] for d in to_index]
    vectors = embeddings_model.embed_documents(texts)

    collection.upsert(
        ids=ids,
        embeddings=vectors,
        documents=texts,
        metadatas=[{"source": "medline", "biomarker": d["id"]} for d in to_index],
    )

    logger.info("Indexed %d MedlinePlus reference entries", len(to_index))


def query_medline(query: str, n_results: int = 3) -> list[str]:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(MEDLINE_COLLECTION)

    query_vector = embeddings_model.embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
    )

    documents = results.get("documents", [[]])[0]
    logger.info("Medline query returned %d results for: %s", len(documents), query)
    return documents