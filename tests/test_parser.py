from ingestion.parser import parse_file
from ingestion.types import DocumentChunk


def test_parse_file_python(tmp_path):
    sample = tmp_path / "sample.py"
    sample.write_text("""
import os


def hello():
    return "hi"
""", encoding="utf-8")
    chunks = parse_file(sample, tmp_path, "repo")
    assert chunks
    assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
    assert chunks[0].imports == ["os"]
