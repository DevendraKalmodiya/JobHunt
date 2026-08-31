import pytest
from src.utils import parse_salary_to_lpa
from src.storage import StorageManager
from src.jobs import JobMatchResult

def test_salary_parsing():
    assert parse_salary_to_lpa("₹5 - ₹8 LPA") == (5.0, 8.0)
    assert parse_salary_to_lpa("3 LPA") == (3.0, 3.0)
    assert parse_salary_to_lpa("₹25,000/month") == (3.0, 3.0)
    assert parse_salary_to_lpa("Competitive Salary") == (None, None)

def test_storage_duplicate_detection(tmp_path):
    storage = StorageManager(data_dir=str(tmp_path))
    storage.record_skipped("Software Engineer", "ABC Corp", "http://example.com/1", "Low score", "123")
    assert storage.is_processed("123", "Software Engineer", "ABC Corp") == True
    assert storage.is_processed("999", "Designer", "XYZ Corp") == False

def test_job_match_schema():
    result = JobMatchResult(
        overall_score=85,
        role_match=90,
        skill_match=80,
        experience_match=85,
        education_match=90,
        location_match=100,
        matching_skills=["Python"],
        missing_skills=[],
        concerns=[],
        reason="Good fit",
        recommendation="APPLY"
    )
    assert result.overall_score == 85
    assert result.recommendation == "APPLY"
