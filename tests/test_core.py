"""
博客核心函数的 pytest 单元测试

覆盖模块: core.py
  - ThemeManager   : 主题初始化 / 切换 / 图标映射 / 持久化
  - MenuState      : 移动端菜单展开收起
  - CardAnimator   : 文章卡片入场动画
  - validate_post  : 文章数据校验
  - filter_posts_* : 文章按分类/标签筛选

运行方式:
    cd "d:/The Shy/tech-blog"
    pytest tests/test_core.py -v
"""

import os
import sys

import pytest

# 确保能导入项目根目录下的 core 模块（须在导入 core 之前执行）
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from core import (
    ThemeManager,
    MenuState,
    CardAnimator,
    validate_post,
    filter_posts_by_category,
    filter_posts_by_tag,
)


# ============================================================
# 一、ThemeManager 主题管理测试
# ============================================================

class TestThemeManager:
    """测试主题初始化、切换、图标映射与持久化逻辑。"""

    def test_get_initial_theme_from_storage(self):
        """
        意图: 当 localStorage 中已保存主题时，应优先返回保存值，
              而不是跟随系统偏好。
        """
        tm = ThemeManager(storage={"theme": "dark"}, system_prefers_dark=False)
        assert tm.get_initial_theme() == "dark"

    def test_get_initial_theme_follows_system_when_no_storage(self):
        """
        意图: 当 storage 为空且系统偏好为深色时，返回 dark。
        """
        tm = ThemeManager(storage={}, system_prefers_dark=True)
        assert tm.get_initial_theme() == "dark"

    def test_get_initial_theme_default_light(self):
        """
        意图: storage 为空且系统非深色模式时，默认返回 light。
        """
        tm = ThemeManager(storage={}, system_prefers_dark=False)
        assert tm.get_initial_theme() == "light"

    def test_get_initial_theme_ignores_invalid_storage_value(self):
        """
        意图: storage 中保存了非法主题值（如 "blue"）时，
              应忽略并回退到系统偏好，避免污染渲染。
        """
        tm = ThemeManager(storage={"theme": "blue"}, system_prefers_dark=False)
        assert tm.get_initial_theme() == "light"

    @pytest.mark.parametrize("current, expected", [
        ("dark", "light"),
        ("light", "dark"),
    ])
    def test_toggle_theme(self, current, expected):
        """
        意图: 验证主题在 dark 与 light 之间正确互斥切换。
        """
        assert ThemeManager.toggle_theme(current) == expected

    def test_toggle_theme_invalid_raises(self):
        """
        意图: 传入非法主题值应抛出 ValueError，防止未知状态扩散。
        """
        with pytest.raises(ValueError):
            ThemeManager.toggle_theme("blue")

    def test_get_theme_icon_dark(self):
        """意图: dark 主题下按钮图标显示太阳 ☀️（表示可切回亮色）。"""
        assert ThemeManager.get_theme_icon("dark") == "☀️"

    def test_get_theme_icon_light(self):
        """意图: light 主题下按钮图标显示月亮 🌙（表示可切到暗色）。"""
        assert ThemeManager.get_theme_icon("light") == "🌙"

    def test_get_theme_icon_invalid_raises(self):
        """意图: 非法主题值求图标应报错。"""
        with pytest.raises(ValueError):
            ThemeManager.get_theme_icon("blue")

    def test_apply_toggle_persists_to_storage(self):
        """
        意图: 调用 apply_toggle 后，新主题应被写入 storage，
              下次 get_initial_theme 能读到该值。
        """
        tm = ThemeManager(storage={}, system_prefers_dark=False)
        new_theme = tm.apply_toggle("light")
        assert new_theme == "dark"
        assert tm.storage["theme"] == "dark"
        assert tm.get_initial_theme() == "dark"


# ============================================================
# 二、MenuState 菜单状态测试
# ============================================================

class TestMenuState:
    """测试移动端导航菜单的展开/收起状态切换。"""

    def test_initial_state_closed(self):
        """意图: 菜单初始为关闭状态。"""
        menu = MenuState()
        assert menu.is_open is False

    def test_toggle_opens_menu(self):
        """意图: 第一次 toggle 后菜单打开。"""
        menu = MenuState()
        assert menu.toggle() is True
        assert menu.is_open is True

    def test_toggle_twice_returns_to_closed(self):
        """意图: 连续 toggle 两次应回到关闭状态。"""
        menu = MenuState()
        menu.toggle()
        assert menu.toggle() is False
        assert menu.is_open is False

    def test_close_always_closes(self):
        """意图: 无论当前状态如何，close 都应使菜单关闭。"""
        menu = MenuState()
        menu.open()
        assert menu.close() is False
        assert menu.is_open is False

    def test_close_when_already_closed(self):
        """意图: 菜单已关闭时再次 close 仍返回 False（幂等）。"""
        menu = MenuState()
        assert menu.close() is False

    def test_open_explicitly(self):
        """意图: 显式调用 open 应使菜单打开。"""
        menu = MenuState()
        assert menu.open() is True


# ============================================================
# 三、CardAnimator 卡片动画测试
# ============================================================

class TestCardAnimator:
    """测试文章卡片滚动入场的样式计算与可见性切换。"""

    def test_register_card_initial_hidden_style(self):
        """
        意图: 注册卡片时初始样式应为隐藏状态：
              opacity=0, transform=translateY(16px)。
        """
        anim = CardAnimator()
        style = anim.register_card("card-1", index=0)
        assert style.opacity == "0"
        assert style.transform == "translateY(16px)"

    def test_register_card_transition_delay_matches_index(self):
        """
        意图: transition 的延迟时间应等于 index * 0.08 秒，
              实现卡片依次淡入的级联效果。
        """
        anim = CardAnimator()
        style = anim.register_card("card-3", index=3)
        # 3 * 0.08 = 0.24
        assert "0.24s" in style.transition

    def test_on_intersect_shows_card(self):
        """
        意图: 卡片进入视口时，opacity 应变为 "1"，
              transform 应变为 "translateY(0)"。
        """
        anim = CardAnimator()
        anim.register_card("card-1", index=0)
        triggered = anim.on_intersect("card-1", is_intersecting=True)
        assert triggered is True
        assert anim.cards["card-1"].opacity == "1"
        assert anim.cards["card-1"].transform == "translateY(0)"
        assert anim.is_visible("card-1") is True

    def test_on_intersect_not_intersecting_no_change(self):
        """
        意图: 卡片未进入视口时，样式不应改变，也不应标记为可见。
        """
        anim = CardAnimator()
        anim.register_card("card-1", index=0)
        triggered = anim.on_intersect("card-1", is_intersecting=False)
        assert triggered is False
        assert anim.cards["card-1"].opacity == "0"
        assert anim.is_visible("card-1") is False

    def test_on_intersect_unregistered_card_raises(self):
        """意图: 对未注册的卡片触发 intersect 应抛 KeyError。"""
        anim = CardAnimator()
        with pytest.raises(KeyError):
            anim.on_intersect("ghost", is_intersecting=True)

    def test_is_visible_default_false(self):
        """意图: 注册后未触发可见性的卡片，is_visible 应为 False。"""
        anim = CardAnimator()
        anim.register_card("card-1", index=0)
        assert anim.is_visible("card-1") is False


# ============================================================
# 四、文章数据校验测试
# ============================================================

class TestValidatePost:
    """测试文章数据结构的完整性与合法性校验。"""

    def _valid_post(self):
        return {
            "title": "React 19 中的 use() Hook 深度解析",
            "date": "2026-09-05",
            "category": "前端",
            "excerpt": "React 19 引入了可以在组件中直接读取 Promise 的 use() Hook。",
            "tags": ["React", "Hooks"],
        }

    def test_valid_post_passes(self):
        """意图: 字段完整且类型正确的文章应通过校验。"""
        assert validate_post(self._valid_post()) is True

    def test_missing_field_raises(self):
        """意图: 缺少必填字段（如 tags）应抛出 ValueError。"""
        post = self._valid_post()
        del post["tags"]
        with pytest.raises(ValueError):
            validate_post(post)

    def test_tags_not_list_raises(self):
        """意图: tags 不是列表时应抛出 TypeError。"""
        post = self._valid_post()
        post["tags"] = "React"  # 应为 list
        with pytest.raises(TypeError):
            validate_post(post)

    def test_empty_title_raises(self):
        """意图: 标题为空字符串时校验不通过。"""
        post = self._valid_post()
        post["title"] = ""
        with pytest.raises(ValueError):
            validate_post(post)

    def test_non_dict_raises(self):
        """意图: 传入非 dict 类型应抛出 TypeError。"""
        with pytest.raises(TypeError):
            validate_post(["not", "a", "dict"])


# ============================================================
# 五、文章筛选测试
# ============================================================

class TestFilterPosts:
    """测试按分类和按标签筛选文章的逻辑。"""

    @pytest.fixture
    def posts(self):
        return [
            {"title": "A", "category": "前端", "tags": ["React", "JS"]},
            {"title": "B", "category": "后端", "tags": ["Go", "性能"]},
            {"title": "C", "category": "前端", "tags": ["Vue", "JS"]},
        ]

    def test_filter_by_category(self, posts):
        """意图: 按"前端"分类筛选，应返回标题为 A 和 C 的两篇。"""
        result = filter_posts_by_category(posts, "前端")
        assert [p["title"] for p in result] == ["A", "C"]

    def test_filter_by_category_no_match(self, posts):
        """意图: 筛选不存在的分类应返回空列表。"""
        assert filter_posts_by_category(posts, "算法") == []

    def test_filter_by_tag(self, posts):
        """意图: 按标签"JS"筛选，应返回 A 和 C（B 不含 JS）。"""
        result = filter_posts_by_tag(posts, "JS")
        assert [p["title"] for p in result] == ["A", "C"]

    def test_filter_by_tag_single_match(self, posts):
        """意图: 按仅出现在一篇文章中的标签筛选，只返回一篇。"""
        result = filter_posts_by_tag(posts, "Go")
        assert [p["title"] for p in result] == ["B"]
