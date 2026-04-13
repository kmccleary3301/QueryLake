from __future__ import annotations

from typing import Iterable, List, Sequence

from sqlmodel import Session, delete, select

from ..database import encryption, sql_db_tables


def _coerce_id_list(values: Iterable[str]) -> List[str]:
    return [str(value) for value in values if value is not None]


def delete_document_dependents(database: Session, document_id: str) -> None:
    """Delete rows that depend on ``document_raw`` in FK-safe order."""

    version_ids = _coerce_id_list(
        database.exec(
            select(sql_db_tables.document_version.id).where(
                sql_db_tables.document_version.document_id == document_id
            )
        ).all()
    )

    if version_ids:
        segment_ids = _coerce_id_list(
            database.exec(
                select(sql_db_tables.document_segment.id).where(
                    sql_db_tables.document_segment.document_version_id.in_(version_ids)
                )
            ).all()
        )

        if segment_ids:
            database.exec(
                delete(sql_db_tables.embedding_record).where(
                    sql_db_tables.embedding_record.segment_id.in_(segment_ids)
                )
            )
            database.exec(
                delete(sql_db_tables.segment_edge).where(
                    sql_db_tables.segment_edge.from_segment_id.in_(segment_ids)
                )
            )
            database.exec(
                delete(sql_db_tables.segment_edge).where(
                    sql_db_tables.segment_edge.to_segment_id.in_(segment_ids)
                )
            )

        database.exec(
            delete(sql_db_tables.document_segment).where(
                sql_db_tables.document_segment.document_version_id.in_(version_ids)
            )
        )
        database.exec(
            delete(sql_db_tables.document_artifact).where(
                sql_db_tables.document_artifact.document_version_id.in_(version_ids)
            )
        )
        database.exec(
            delete(sql_db_tables.segmentation_run).where(
                sql_db_tables.segmentation_run.document_version_id.in_(version_ids)
            )
        )
        database.exec(
            delete(sql_db_tables.document_version).where(
                sql_db_tables.document_version.id.in_(version_ids)
            )
        )

    database.exec(
        delete(sql_db_tables.DocumentChunk).where(
            sql_db_tables.DocumentChunk.document_id == document_id
        )
    )


def delete_document_record(database: Session, document: sql_db_tables.document_raw) -> None:
    """Delete one document and its dependent rows, including blob bookkeeping."""

    delete_document_dependents(database, str(document.id))
    if getattr(document, "blob_id", None):
        encryption.aes_delete_file_from_zip_blob(database, str(document.id), commit=False)
    database.delete(document)


def delete_collection_documents(
    database: Session,
    documents: Sequence[sql_db_tables.document_raw],
) -> None:
    for document in documents:
        delete_document_record(database, document)
