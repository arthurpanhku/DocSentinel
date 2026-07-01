from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.core.db import get_session
from app.main import app


def _override_session(engine):
    def _override():
        with Session(engine) as session:
            yield session

    return _override


def test_oscal_catalog_export_contains_controls_and_opencre_links(client):
    response = client.get("/api/v1/oscal/catalog?framework_ids=nist-ssdf")

    assert response.status_code == 200
    payload = response.json()
    catalog = payload["data"]["catalog"]
    assert catalog["metadata"]["oscal-version"] == "1.1.2"
    assert payload["meta"]["format"] == "oscal-catalog"
    assert catalog["groups"]

    controls = [
        control for group in catalog["groups"] for control in group.get("controls", [])
    ]
    assert controls
    first = controls[0]
    assert first["id"]
    assert any(
        link["href"].startswith("https://opencre.org/") for link in first["links"]
    )
    assert any(prop["name"] == "source-framework" for prop in first["props"])


def test_project_oscal_assessment_results_include_evidence_and_findings(
    client,
    tmp_path,
):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'oscal.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    app.dependency_overrides[get_session] = _override_session(engine)
    try:
        created = client.post(
            "/api/v1/projects",
            json={
                "name": "OSCAL Export Project",
                "description": "Public test fixture for OSCAL export.",
                "organization": "Example Org",
                "risk_tier": "high",
                "compliance_frameworks": ["nist-ssdf"],
            },
        )
        assert created.status_code == 201
        project_id = created.json()["data"]["id"]

        controls = client.get(f"/api/v1/projects/{project_id}/controls")
        assert controls.status_code == 200
        control = controls.json()["data"][0]

        evidence = client.post(
            (
                f"/api/v1/projects/{project_id}/controls/"
                f"{control['control_id']}/evidence"
            ),
            json={
                "evidence_type": "link",
                "url": "https://example.com/evidence/control-review",
                "content": "Public evidence summary for OSCAL export.",
            },
        )
        assert evidence.status_code == 200

        exported = client.get(f"/api/v1/projects/{project_id}/oscal/assessment-results")
        assert exported.status_code == 200
        payload = exported.json()
    finally:
        app.dependency_overrides.clear()

    assert payload["meta"]["format"] == "oscal-assessment-results"
    results = payload["data"]["assessment-results"]
    assert results["metadata"]["oscal-version"] == "1.1.2"
    result = results["results"][0]
    assert result["reviewed-controls"]["control-selections"][0]["include-controls"]
    assert result["observations"]
    assert result["observations"][0]["relevant-evidence"][0]["href"].startswith(
        "https://example.com/evidence/"
    )
    assert result["findings"]
    assert result["findings"][0]["target"]["status"]["state"] in {
        "under-review",
        "not-applicable",
        "satisfied",
        "not-satisfied",
    }
