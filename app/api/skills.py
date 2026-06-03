"""
API endpoints for managing skills (personas).
"""

from fastapi import APIRouter, HTTPException

from app.agent.skills_service import get_skill_service
from app.models.skill import Skill, SkillCreate, SkillUpdate

router = APIRouter()


@router.get("/", response_model=list[Skill])
async def list_skills():
    """List all available skills (built-in + custom)."""
    service = get_skill_service()
    return service.list_skills()


@router.get("/{skill_id}", response_model=Skill)
async def get_skill(skill_id: str):
    """Get a specific skill definition."""
    service = get_skill_service()
    skill = service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("/", response_model=Skill)
async def create_skill(skill_in: SkillCreate):
    """Create a new custom skill."""
    service = get_skill_service()
    try:
        return service.create_skill(skill_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{skill_id}", response_model=Skill)
async def update_skill(skill_id: str, skill_in: SkillUpdate):
    """Update an existing custom skill."""
    service = get_skill_service()
    try:
        return service.update_skill(skill_id, skill_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{skill_id}")
async def delete_skill(skill_id: str):
    """Delete a custom skill."""
    service = get_skill_service()
    try:
        service.delete_skill(skill_id)
        return {"message": "Skill deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
