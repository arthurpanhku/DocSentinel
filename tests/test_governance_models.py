from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.core.security import ensure_role
from app.models.governance import ControlInstance, GateSubmission, Project, SubAgentRun
from app.models.user import VALID_ROLES, User


def test_project_submission_control_crud(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'governance.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            username="client",
            email="client@example.com",
            hashed_password="hash",
            role="client",
        )
        session.add(user)
        session.flush()
        user_id = user.id

        project = Project(
            name="AI Gateway",
            owner_id=user_id,
            compliance_frameworks=["nist-ssdf"],
        )
        session.add(project)
        session.flush()

        submission = GateSubmission(project_id=project.id, gate_number=3)
        control = ControlInstance(
            project_id=project.id,
            control_id="SCD-001",
            framework_id="generic-ssdlc",
            title="Threat model reviewed",
            normalized_requirement="Threat model must be reviewed before release.",
            expected_evidence=["threat model"],
            review_focus=["design coverage"],
        )
        session.add(submission)
        session.add(control)
        session.commit()

        stored_project = session.exec(select(Project)).one()
        stored_submission = session.exec(select(GateSubmission)).one()
        stored_control = session.exec(select(ControlInstance)).one()

    assert stored_project.owner_id == user_id
    assert stored_project.compliance_frameworks == ["nist-ssdf"]
    assert stored_submission.project_id == stored_project.id
    assert stored_submission.gate_number == 3
    assert stored_control.project_id == stored_project.id
    assert stored_control.status == "pending"


def test_governance_roles_and_transition_helpers():
    assert {"client", "security_reviewer", "security_approver", "admin"} <= VALID_ROLES
    reviewer = SimpleNamespace(role="security_reviewer", is_superuser=False)
    assert ensure_role(reviewer, "security_reviewer") is reviewer

    with pytest.raises(HTTPException) as exc:
        ensure_role(SimpleNamespace(role="client", is_superuser=False), "admin")
    assert exc.value.status_code == 403

    run = SubAgentRun(
        project_id="00000000-0000-0000-0000-000000000000",
        gate="gate3",
        sub_agent_key="scd",
    )
    assert run.can_transition_to("draft") is True
    assert run.can_transition_to("approved") is False
