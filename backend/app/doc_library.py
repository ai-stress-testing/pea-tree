"""The Docs library — the document types a sprint can hold (PRD §5) and a
short markdown starter for each. Starters are just scaffolding; the split
editor and the agents fill them in.
"""

# type -> human label. Order is the library's display order.
DOC_TYPES: dict[str, str] = {
    "feature-request": "Feature Request",
    "customer-feedback": "Customer Feedback",
    "business-case": "Business Case",
    "prd": "PRD",
    "mvp": "MVP",
    "roadmap": "Roadmap",
    "acceptance-criteria": "Acceptance Criteria",
    "release-goals": "Release Goals",
    "mermaid-wireframe": "Mermaid Wireframe",
    "user-flows": "User Flows",
    "design-spec": "Design Spec",
    "accessibility-checklist": "Accessibility Checklist",
    "design-review": "Design Review",
    "architecture": "Architecture",
    "srs": "SRS",
    "api-spec": "API Spec",
    "database-design": "Database Design",
    "sequence-diagram": "Sequence Diagram",
    "risk-assessment": "Risk Assessment",
    "implementation-plan": "Implementation Plan",
    "issue": "Issue",
    "sprint-board": "Sprint Board",
    "engineering-notes": "Engineering Notes",
    "test-plan": "Test Plan",
    "security-review": "Security Review",
}

# Category each doc type belongs to (Feature 2). Order defines display order.
CATEGORIES: list[str] = [
    "Intake", "Project Management", "Design", "Engineering",
    "Development", "Testing", "Deliverables / Standards",
]
DOC_CATEGORY: dict[str, str] = {
    "feature-request": "Intake", "customer-feedback": "Intake", "business-case": "Intake",
    "prd": "Project Management", "mvp": "Project Management", "roadmap": "Project Management",
    "acceptance-criteria": "Project Management", "release-goals": "Project Management",
    "sprint-board": "Project Management",
    "mermaid-wireframe": "Design", "user-flows": "Design", "design-spec": "Design",
    "accessibility-checklist": "Design", "design-review": "Design",
    "architecture": "Engineering", "srs": "Engineering", "api-spec": "Engineering",
    "database-design": "Engineering", "sequence-diagram": "Engineering",
    "implementation-plan": "Development", "issue": "Development", "engineering-notes": "Development",
    "test-plan": "Testing",
    "risk-assessment": "Deliverables / Standards", "security-review": "Deliverables / Standards",
}

_MERMAID_STARTER = """# {label}

```mermaid
flowchart LR
  A[Start] --> B[Next]
```
"""


def starter(doc_type: str, title: str) -> str:
    label = DOC_TYPES.get(doc_type, doc_type)
    if doc_type in ("mermaid-wireframe", "sequence-diagram"):
        return _MERMAID_STARTER.format(label=title or label)
    return f"# {title or label}\n\n_{label} — start writing, or ask an agent to draft this._\n"


def library() -> list[dict]:
    return [
        {"type": t, "label": lbl, "category": DOC_CATEGORY.get(t, "Deliverables / Standards")}
        for t, lbl in DOC_TYPES.items()
    ]
