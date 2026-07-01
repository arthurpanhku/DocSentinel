"""Application services shared by REST and agent protocols."""

__all__ = ["assessment_service"]


def __getattr__(name: str):
    if name == "assessment_service":
        from .assessment_service import assessment_service

        return assessment_service
    raise AttributeError(name)
