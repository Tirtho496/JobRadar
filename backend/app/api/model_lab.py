import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select

from app.auth import require_api_key
from app.config import get_settings
from app.core.embedding import get_embedding_service
from app.core.evaluation import evaluate
from app.core.profile import get_profile
from app.db import SessionDep
from app.models import ModelEvaluation

router = APIRouter(prefix="/api/model-lab", tags=["model-lab"], dependencies=[Depends(require_api_key)])
settings = get_settings()


@router.get("")
async def list_evaluations(session: SessionDep) -> dict:
    rows = list(
        (await session.scalars(select(ModelEvaluation).order_by(desc(ModelEvaluation.created_at)).limit(30))).all()
    )
    return {
        "active_model": settings.embedding_model if settings.embedding_enabled else "disabled",
        "results": [
            {
                "id": row.id,
                "model_name": row.model_name,
                "dataset_name": row.dataset_name,
                "precision_at_10": row.precision_at_10,
                "ndcg_at_10": row.ndcg_at_10,
                "mean_latency_ms": row.mean_latency_ms,
                "notes": row.notes,
                "created_at": row.created_at,
            }
            for row in rows
        ],
    }


@router.post("/run")
async def run_evaluation(session: SessionDep) -> dict:
    dataset = settings.data_dir / "evaluation" / "job_relevance_v1.jsonl"
    results = await asyncio.to_thread(evaluate, get_profile(), get_embedding_service(), dataset)
    for result in results:
        session.add(
            ModelEvaluation(
                model_name=result["model_name"],
                dataset_name=dataset.name,
                precision_at_10=result["precision_at_10"],
                ndcg_at_10=result["ndcg_at_10"],
                mean_latency_ms=result["mean_latency_ms"],
                notes=result["notes"],
            )
        )
    await session.commit()
    return {"status": "completed", "results": results}
