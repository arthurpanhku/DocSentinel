"""
Skills Management Service (InMemory / File based for now).
"""

import json
from pathlib import Path

from app.agent.skills_registry import get_builtin_skills
from app.models.skill import Skill, SkillCreate, SkillUpdate


class SkillService:
    def __init__(self, storage_path: str = "./data/skills.json"):
        self.storage_path = Path(storage_path)
        self.custom_skills: dict[str, Skill] = {}
        self._load_custom_skills()

    def _load_custom_skills(self):
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    s = Skill(**item)
                    self.custom_skills[s.id] = s
        except Exception as e:
            print(f"Error loading skills: {e}")

    def _save_custom_skills(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [s.model_dump() for s in self.custom_skills.values()]
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_skills(self) -> list[Skill]:
        builtin = get_builtin_skills()
        custom = list(self.custom_skills.values())
        return builtin + custom

    def get_skill(self, skill_id: str) -> Skill | None:
        if skill_id in self.custom_skills:
            return self.custom_skills[skill_id]
        for s in get_builtin_skills():
            if s.id == skill_id:
                return s
        return None

    def create_skill(self, skill_in: SkillCreate) -> Skill:
        if self.get_skill(skill_in.id):
            raise ValueError(f"Skill with ID {skill_in.id} already exists.")

        skill = Skill(
            id=skill_in.id,
            name=skill_in.name,
            description=skill_in.description,
            system_prompt=skill_in.system_prompt,
            risk_focus=skill_in.risk_focus,
            compliance_frameworks=skill_in.compliance_frameworks,
            is_builtin=False,
        )
        self.custom_skills[skill.id] = skill
        self._save_custom_skills()
        return skill

    def update_skill(self, skill_id: str, skill_in: SkillUpdate) -> Skill:
        if skill_id not in self.custom_skills:
            # Check built-in
            if self.get_skill(skill_id):
                raise ValueError("Cannot modify built-in skills.")
            raise ValueError("Skill not found.")

        current = self.custom_skills[skill_id]
        updated_data = skill_in.model_dump(exclude_unset=True)
        updated_skill = current.model_copy(update=updated_data)

        self.custom_skills[skill_id] = updated_skill
        self._save_custom_skills()
        return updated_skill

    def delete_skill(self, skill_id: str):
        if skill_id in self.custom_skills:
            del self.custom_skills[skill_id]
            self._save_custom_skills()
        elif self.get_skill(skill_id):
            raise ValueError("Cannot delete built-in skills.")
        else:
            raise ValueError("Skill not found.")


# Singleton
_skill_service = None


def get_skill_service() -> SkillService:
    global _skill_service
    if _skill_service is None:
        _skill_service = SkillService()
    return _skill_service
