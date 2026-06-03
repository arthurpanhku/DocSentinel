
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_list_skills():
    response = client.get("/api/v1/skills/")
    assert response.status_code == 200
    skills = response.json()
    assert len(skills) >= 4  # At least 4 built-in skills

    # Check for specific built-in skill
    iso_auditor = next((s for s in skills if s["id"] == "iso-27001-auditor"), None)
    assert iso_auditor is not None
    assert iso_auditor["is_builtin"] is True

def test_list_ssdlc_builtin_skills():
    response = client.get("/api/v1/skills/")
    assert response.status_code == 200
    ids = {skill["id"] for skill in response.json()}
    assert {
        "ssdlc-requirements",
        "ssdlc-design",
        "ssdlc-development",
        "ssdlc-testing",
        "ssdlc-deployment",
        "ssdlc-operations",
    }.issubset(ids)

def test_create_custom_skill():
    from uuid import uuid4
    unique_id = f"custom-pci-{uuid4()}"
    new_skill = {
        "id": unique_id,
        "name": "PCI DSS Auditor",
        "description": "Checks for credit card data security",
        "system_prompt": "You are a PCI DSS auditor...",
        "risk_focus": ["Cardholder Data", "Encryption"],
        "compliance_frameworks": ["PCI DSS v4.0"]
    }

    # Create
    response = client.post("/api/v1/skills/", json=new_skill)
    assert response.status_code == 200
    created_skill = response.json()
    assert created_skill["id"] == unique_id
    assert created_skill["is_builtin"] is False

    # Verify it appears in list
    response = client.get("/api/v1/skills/")
    skills = response.json()
    found = next((s for s in skills if s["id"] == unique_id), None)
    assert found is not None

    # Cleanup
    client.delete(f"/api/v1/skills/{unique_id}")

def test_update_custom_skill():
    # First create a skill (or rely on previous test order, but better to be independent)
    skill_id = "update-test-skill"
    client.post("/api/v1/skills/", json={
        "id": skill_id,
        "name": "Original Name",
        "description": "Desc",
        "system_prompt": "Prompt",
    })

    # Update
    update_data = {"name": "Updated Name", "risk_focus": ["New Focus"]}
    response = client.put(f"/api/v1/skills/{skill_id}", json=update_data)
    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Updated Name"
    assert updated["risk_focus"] == ["New Focus"]

    # Verify persistence
    response = client.get(f"/api/v1/skills/{skill_id}")
    assert response.json()["name"] == "Updated Name"

def test_delete_custom_skill():
    skill_id = "delete-test-skill"
    client.post("/api/v1/skills/", json={
        "id": skill_id,
        "name": "To Be Deleted",
        "description": "Desc",
        "system_prompt": "Prompt",
    })

    # Delete
    response = client.delete(f"/api/v1/skills/{skill_id}")
    assert response.status_code == 200

    # Verify gone
    response = client.get(f"/api/v1/skills/{skill_id}")
    assert response.status_code == 404

def test_cannot_modify_builtin_skill():
    builtin_id = "iso-27001-auditor"

    # Try Update
    response = client.put(f"/api/v1/skills/{builtin_id}", json={"name": "Hacked Auditor"})
    assert response.status_code == 400
    assert "Cannot modify built-in" in response.text

    # Try Delete
    response = client.delete(f"/api/v1/skills/{builtin_id}")
    assert response.status_code == 400
    assert "Cannot delete built-in" in response.text
