"""
博客核心业务逻辑模块（Python 版本）

将前端 js/main.js 中的核心逻辑抽象为可独立测试的纯函数/类，
便于使用 pytest 进行单元测试。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set


# ============================================================
# 1. 主题管理（对应 main.js 中的 initTheme / toggle / updateThemeIcon）
# ============================================================

class ThemeManager:
    """管理博客的浅色/深色主题切换。"""

    VALID_THEMES = ("light", "dark")
    OPPOSITE_THEME = {"dark": "light", "light": "dark"}  # 主题互斥映射
    THEME_ICONS = {"dark": "☀️", "light": "🌙"}  # 主题对应图标

    @staticmethod
    def _validate_theme(theme: str) -> None:
        """校验主题值合法性，非法值统一抛出 ValueError。"""
        if theme not in ThemeManager.VALID_THEMES:
            raise ValueError(f"非法主题值: {theme}")

    def __init__(self, storage: Optional[Dict[str, str]] = None,
                 system_prefers_dark: bool = False):
        """初始化主题管理器。

        Args:
            storage: 模拟浏览器 localStorage 的字典。
            system_prefers_dark: 系统是否偏好深色主题。
        """
        self.storage: Dict[str, str] = storage if storage is not None else {}
        self.system_prefers_dark = system_prefers_dark

    def get_initial_theme(self) -> str:
        """
        对应 JS:
            const saved = localStorage.getItem("theme");
            const prefersDark = window.matchMedia(
                "(prefers-color-scheme: dark)").matches;
            const theme = saved || (prefersDark ? "dark" : "light");
        """
        saved = self.storage.get("theme")
        if saved in self.VALID_THEMES:
            return saved
        return "dark" if self.system_prefers_dark else "light"

    @staticmethod
    def toggle_theme(current: str) -> str:
        """
        对应 JS:
            const next = current === "dark" ? "light" : "dark";
        """
        ThemeManager._validate_theme(current)
        return ThemeManager.OPPOSITE_THEME[current]

    @staticmethod
    def get_theme_icon(theme: str) -> str:
        """
        对应 JS:
            themeToggle.textContent = theme === "dark" ? "☀️" : "🌙";
        """
        ThemeManager._validate_theme(theme)
        return ThemeManager.THEME_ICONS[theme]

    def apply_toggle(self, current: str) -> str:
        """执行一次主题切换并持久化到 storage，返回新主题。"""
        new_theme = self.toggle_theme(current)
        self.storage["theme"] = new_theme
        return new_theme


# ============================================================
# 2. 移动端菜单状态（对应 main.js 中的 nav.classList.toggle/remove）
# ============================================================

class MenuState:
    """管理移动端导航菜单的展开/收起状态。"""

    def __init__(self):
        """初始化菜单为关闭状态。"""
        self.is_open: bool = False

    def toggle(self) -> bool:
        """对应 JS: nav.classList.toggle("open"); 返回切换后的状态。"""
        self.is_open = not self.is_open
        return self.is_open

    def close(self) -> bool:
        """对应 JS: nav.classList.remove("open"); 点击菜单项后关闭菜单。"""
        self.is_open = False
        return self.is_open

    def open(self) -> bool:
        """显式打开菜单。"""
        self.is_open = True
        return self.is_open


# ============================================================
# 3. 文章卡片入场动画（对应 main.js 中的 IntersectionObserver 回调）
# ============================================================

@dataclass
class CardStyle:
    opacity: str = "0"
    transform: str = "translateY(16px)"
    transition: str = ""


class CardAnimator:
    """管理文章卡片滚动进入视口时的淡入动画。"""

    def __init__(self):
        """初始化空的卡片样式表与可见集合。"""
        # card_id -> style
        self.cards: Dict[str, CardStyle] = {}
        self.visible_cards: Set[str] = set()

    def register_card(self, card_id: str, index: int) -> CardStyle:
        """
        对应 JS:
            card.style.opacity = "0";
            card.style.transform = "translateY(16px)";
            card.style.transition =
                `opacity 0.5s ${i * 0.08}s, transform 0.5s ${i * 0.08}s`;
        """
        delay = index * 0.08
        style = CardStyle(
            transition=f"opacity 0.5s {delay}s, transform 0.5s {delay}s",
        )
        self.cards[card_id] = style
        return style

    def on_intersect(self, card_id: str, is_intersecting: bool) -> bool:
        """
        对应 JS IntersectionObserver 回调:
            if (entry.isIntersecting) {
              entry.target.style.opacity = "1";
              entry.target.style.transform = "translateY(0)";
            }
        返回 True 表示卡片被触发了可见动画。
        """
        if card_id not in self.cards:
            raise KeyError(f"未注册的卡片: {card_id}")
        if is_intersecting:
            style = self.cards[card_id]
            style.opacity = "1"
            style.transform = "translateY(0)"
            self.visible_cards.add(card_id)
            return True
        return False

    def is_visible(self, card_id: str) -> bool:
        """查询卡片是否已触发可见动画。"""
        return card_id in self.visible_cards


# ============================================================
# 4. 文章数据校验（对应 index.html 中文章卡片的数据结构）
# ============================================================

REQUIRED_POST_FIELDS = ("title", "date", "category", "excerpt", "tags")


def validate_post(post: Dict[str, object]) -> bool:
    """
    校验一篇文章的数据结构是否完整合法。
    合法字段示例:
        {
            "title": "...",
            "date": "2026-09-10",
            "category": "前端",
            "excerpt": "...",
            "tags": ["React", "Hooks"],
        }
    """
    if not isinstance(post, dict):
        raise TypeError("文章数据必须是 dict")

    missing = [f for f in REQUIRED_POST_FIELDS if f not in post]
    if missing:
        raise ValueError(f"文章缺少必填字段: {missing}")

    if not isinstance(post["tags"], list):
        raise TypeError("tags 字段必须是列表")

    title = post["title"]
    if not isinstance(title, str) or not title:
        raise ValueError("title 必须是非空字符串")

    return True


def filter_posts_by_category(posts: List[Dict[str, object]],
                             category: str) -> List[Dict[str, object]]:
    """按分类筛选文章。"""
    return [p for p in posts if p.get("category") == category]


def filter_posts_by_tag(posts: List[Dict[str, object]],
                        tag: str) -> List[Dict[str, object]]:
    """按标签筛选文章（文章包含该标签即命中）。"""
    return [p for p in posts if tag in p.get("tags", [])]
