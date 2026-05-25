"""Dice roller — /roll for players and DMs alike."""
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from bot.generators import dice as _dice


class DiceCog(commands.Cog, name="Dice"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="roll", description="Roll dice — 1d20, 2d6+3, 4d6kh3, 1d20 adv …")
    @app_commands.describe(
        expression="Dice expression: 1d20+5 · 4d6kh3 · 2d8-1 · 1d20 adv · 1d20 dis",
        secret="Only you see the result — for DM secret rolls",
    )
    async def roll_cmd(
        self,
        interaction: discord.Interaction,
        expression: str,
        secret: bool = False,
    ) -> None:
        try:
            result = _dice.roll(expression)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        # Build per-die display — bold max, strikethrough dropped
        remaining_kept = list(result.kept)
        parts: list[str] = []
        for d in result.rolls:
            if d in remaining_kept:
                remaining_kept.remove(d)
                if d == result.die_sides:
                    parts.append(f"**{d}**")
                elif d == 1 and result.die_sides != 2:
                    parts.append(f"*{d}*")
                else:
                    parts.append(str(d))
            else:
                parts.append(f"~~{d}~~")

        dice_str = "[" + ", ".join(parts) + "]"
        if result.modifier:
            sign = "+" if result.modifier > 0 else ""
            dice_str += f" {sign}{result.modifier}"

        if result.is_crit:
            colour = 0xFFD700
            banner = "⚡ **CRITICAL HIT!**"
        elif result.is_fumble:
            colour = 0xCC2222
            banner = "💀 **Critical Fumble.**"
        else:
            colour = 0x5865F2
            banner = ""

        embed = discord.Embed(colour=colour, description=banner or None)
        embed.add_field(name="Roll", value=f"`{result.label}`", inline=True)
        embed.add_field(name="Dice", value=dice_str, inline=True)
        embed.add_field(name="Total", value=f"**{result.total}**", inline=True)
        embed.set_footer(text=f"Rolled by {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed, ephemeral=secret)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiceCog(bot))
