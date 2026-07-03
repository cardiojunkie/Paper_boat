from collections.abc import Generator
from io import BytesIO
from struct import pack

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.main import app


@pytest.fixture()
def db() -> Generator[Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db: Session) -> Generator[TestClient]:
    def override_db() -> Generator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def workbook_bytes(headers: list[str], rows: list[list[object]]) -> bytes:
    book = Workbook()
    sheet = book.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    stream = BytesIO()
    book.save(stream)
    return stream.getvalue()


def xls_workbook_bytes() -> bytes:
    def record(opcode: int, data: bytes = b"") -> bytes:
        return pack("<HH", opcode, len(data)) + data

    def label(row: int, column: int, value: str) -> bytes:
        encoded = value.encode("latin1")
        return record(0x0004, pack("<HH3sB", row, column, b"\0\0\0", len(encoded)) + encoded)

    # ponytail: tiny BIFF2 stream; no writer dependency just to create a legacy .xls fixture.
    return b"".join(
        [
            record(0x0009, pack("<HH", 0x0002, 0x0010)),
            label(0, 0, "SKU"),
            label(0, 1, "name"),
            label(0, 2, "attributes__lulu_product_type"),
            label(1, 0, "00123"),
            label(1, 1, "Legacy Washer"),
            label(1, 2, "Appliance"),
            record(0x000A),
        ]
    )
