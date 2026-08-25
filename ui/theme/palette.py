"""Design tokens for light and dark themes — a restrained, professional
neutral palette with a single accent color, per the spec's UI guidance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    name: str
    window: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_text: str
    success: str
    warning: str
    danger: str


LIGHT = Palette(
    name="light", window="#F5F6F8", surface="#FFFFFF", surface_alt="#EFF1F4",
    border="#E2E5EA", text="#181B20", text_muted="#6B7280",
    accent="#4F46E5", accent_hover="#4338CA", accent_text="#FFFFFF",
    success="#16A34A", warning="#D97706", danger="#DC2626",
)

DARK = Palette(
    name="dark", window="#131417", surface="#1C1E23", surface_alt="#25272E",
    border="#2E3138", text="#EDEEF1", text_muted="#9298A2",
    accent="#6366F1", accent_hover="#818CF8", accent_text="#FFFFFF",
    success="#22C55E", warning="#F59E0B", danger="#EF4444",
)
