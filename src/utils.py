import re
from typing import Tuple, Optional

def parse_salary_to_lpa(salary_str: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    if not salary_str:
        return None, None
    
    clean_str = salary_str.replace(",", "").strip()
    
    # Check for LPA format (e.g. ₹5 - ₹8 LPA or 6 LPA)
    lpa_match = re.findall(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*LPA", clean_str, re.IGNORECASE)
    if lpa_match:
        min_val = float(lpa_match[0][0])
        max_val = float(lpa_match[0][1]) if lpa_match[0][1] else min_val
        return min_val, max_val

    # Check monthly salary (e.g. ₹25,000/month or 25000 - 50000 / month)
    monthly_match = re.findall(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*(?:/month|per month|pm)", clean_str, re.IGNORECASE)
    if monthly_match:
        min_m = float(monthly_match[0][0])
        max_m = float(monthly_match[0][1]) if monthly_match[0][1] else min_m
        min_lpa = round((min_m * 12) / 100000, 2)
        max_lpa = round((max_m * 12) / 100000, 2)
        return min_lpa, max_lpa

    # Check raw numbers in lakhs
    lakh_match = re.findall(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*lakh", clean_str, re.IGNORECASE)
    if lakh_match:
        min_val = float(lakh_match[0][0])
        max_val = float(lakh_match[0][1]) if lakh_match[0][1] else min_val
        return min_val, max_val

    return None, None
