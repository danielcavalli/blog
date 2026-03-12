"""CV data loading and schema validation.

Loads structured CV data from cv_data.yaml and validates it against
the expected schema before the build uses it.
"""

import yaml

from paths import CV_DATA_FILE


def load_cv_data():
    """Load and validate structured CV data from cv_data.yaml.

    cv_data.yaml is the single source of truth for English CV content.
    The Portuguese CV is produced by translating this function's output at
    build time.

    Schema validation replaces the old heuristic markdown parsing:
    required top-level keys must exist and be non-empty, contact must
    include email/linkedin/github, and experience/education entries
    must have their required sub-fields.

    Returns:
        dict | None: Structured CV data with keys: name, tagline, location,
            contact, skills, languages_spoken, summary, experience, education.
            Returns None only if the file does not exist.

    Raises:
        SystemExit: If required fields are missing or empty.
    """
    if not CV_DATA_FILE.exists():
        print(f"Warning: CV data file not found at {CV_DATA_FILE}")
        return None

    with open(CV_DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            cv_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error: Failed to parse {CV_DATA_FILE}: {e}")
            raise SystemExit(1)

    if not isinstance(cv_data, dict):
        print(f"Error: {CV_DATA_FILE} must be a YAML mapping, got {type(cv_data).__name__}")
        raise SystemExit(1)

    # --- Schema validation ---------------------------------------------------
    errors = []

    # Required top-level scalar fields
    for key in ('name', 'summary'):
        if not cv_data.get(key):
            errors.append(f"'{key}' is missing or empty")

    # Required top-level list fields
    for key in ('experience', 'education', 'skills'):
        val = cv_data.get(key)
        if not val or not isinstance(val, list):
            errors.append(f"'{key}' is missing or not a list")

    # Contact sub-fields
    contact = cv_data.get('contact')
    if not contact or not isinstance(contact, dict):
        errors.append("'contact' is missing or not a mapping")
    else:
        for key in ('email', 'linkedin', 'github'):
            if not contact.get(key):
                errors.append(f"contact.{key} is missing or empty")

    # Experience entry validation
    for i, exp in enumerate(cv_data.get('experience') or []):
        for key in ('title', 'company', 'period'):
            if not exp.get(key):
                errors.append(f"experience[{i}].{key} is missing or empty")
        # Ensure defaults for optional fields
        exp.setdefault('location', 'Brazil')
        exp.setdefault('description', '')
        exp.setdefault('achievements', [])

    # Education entry validation
    for i, edu in enumerate(cv_data.get('education') or []):
        for key in ('degree', 'school', 'period'):
            if not edu.get(key):
                errors.append(f"education[{i}].{key} is missing or empty")

    if errors:
        print(
            f"Error: {CV_DATA_FILE} validation failed:\n"
            + '\n'.join(f"  - {e}" for e in errors)
        )
        raise SystemExit(1)

    # Warn on non-critical but expected fields
    if not cv_data.get('tagline'):
        print("Warning: CV tagline is empty")
    if not cv_data.get('location'):
        print("Warning: CV location is empty")
    if not cv_data.get('languages_spoken'):
        print("Warning: CV languages_spoken is empty")

    return cv_data
