"""Team management module — roles, permissions and invitations (Final Gaps)."""
from app.modules.team.models import Role, TeamInvitation
from app.modules.team.permissions import require_permission
from app.modules.team.router import router
from app.modules.team.service import TeamService

__all__ = ["router", "TeamService", "Role", "TeamInvitation", "require_permission"]
