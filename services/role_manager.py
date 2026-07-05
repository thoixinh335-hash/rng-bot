import discord
import logging
from services.config_service import ConfigService

logger = logging.getLogger("rng_bot")

class RoleManager:
    def __init__(self):
        self.config_service = ConfigService()

    async def update_discord_roles(self, member: discord.Member, new_role_id: int) -> None:
        if not member.guild.me.guild_permissions.manage_roles:
            logger.warning(f"Bot thiếu quyền 'Manage Roles' tại server: {member.guild.name}")
            return

        all_rng_roles = self.config_service.get_roles_list()
        all_rng_ids = {r["role_id"] for r in all_rng_roles}
        
        # Lọc danh sách các role hiện tại của user để gỡ bỏ
        roles_to_remove = [role for role in member.roles if role.id in all_rng_ids and role.id != new_role_id]
        
        target_role = member.guild.get_role(new_role_id)
        
        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="RNG Bot - Gỡ bỏ danh hiệu cũ")
            if target_role and target_role not in member.roles:
                await member.add_roles(target_role, reason="RNG Bot - Cấp danh hiệu mới vừa Roll")
        except discord.Forbidden:
            logger.error(f"Không thể chỉnh sửa vai trò cho {member.name}. Thứ tự vai trò của Bot có thể nằm dưới vai trò cần cấp.")
        except discord.HTTPException as e:
            logger.error(f"Lỗi HTTP khi cập nhật vai trò: {e}")