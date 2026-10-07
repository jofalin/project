from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .production_models import SOPDocument

class PostgresSOPRetriever:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, embedding: list[float], limit: int = 5) -> list[dict]:
        stmt = (
            select(SOPDocument.id, SOPDocument.title, SOPDocument.content, SOPDocument.metadata_json)
            .where(SOPDocument.embedding.is_not(None))
            .order_by(SOPDocument.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        return [{"id": r.id, "title": r.title, "content": r.content, "metadata": r.metadata_json} for r in rows]
