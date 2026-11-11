# CodeNest · 个人技术博客

一个纯前端的个人技术博客，零构建、零后端，双击 `index.html` 即可运行；同时把页面里的三块交互逻辑抽成了可被 `pytest` 直接测试的 Python 模块，用于验证"行为正确"而不只是"看起来对"。

## 解决了什么问题

写博客这件事本身不难，难的是**长期维护**：

- 主题色、圆角、阴影散落在各处，换一次配色要改几十行 → 现在全部收敛为 `css/style.css` 顶部的 13 个 CSS 变量，深浅两套主题各定义一次，改一个值全站生效。
- 深色/浅色切换每次刷新都被重置 → 现在用 `localStorage` 记住选择，首次访问则跟随系统 `prefers-color-scheme`。
- 交互逻辑写在 JS 里，改完只能靠肉眼点一遍验证 → 现在把逻辑等价重写成 `core.py` 的纯函数/类，用 32 条单元测试覆盖边界情况（非法主题值、未注册卡片、缺字段的文章等）。

## 目录结构

```
tech-blog/
├── index.html          首页：Hero 区 + 文章卡片列表 + 分类/标签侧栏
├── post.html           文章详情页
├── about.html          关于页
├── css/
│   └── style.css       全部样式；顶部 :root[data-theme] 定义深浅两套变量
├── js/
│   └── main.js         主题切换、移动端菜单、卡片入场动画
├── core.py             与 main.js 行为等价的 Python 实现，供测试使用
├── tests/
│   └── test_core.py    32 条 pytest 用例，5 个测试类
├── docs/
│   └── 技术文档.md      技术文档初稿（设计动机、实现、出处核对）
└── .gitignore
```

## 两条入口

**1）网页版（给人看）**

直接在浏览器打开 `index.html`，或用任意静态服务器：

```bash
python -m http.server 8000
# 然后访问 http://localhost:8000
```

**2）命令行（给机器看）**

```bash
pip install pytest
python -m pytest tests/ -v
```

预期输出 `32 passed`。

## 输入 → 处理 → 输出

| 模块 | 输入 | 处理 | 输出 |
| --- | --- | --- | --- |
| 主题切换 `ThemeManager` | localStorage 里的 `theme` 值、系统 `prefers-color-scheme` | 校验合法性 → 已存值优先，否则跟随系统 → 取反 | `data-theme` 属性值 + 对应图标（🌙/☀️），并回写 localStorage |
| 移动端菜单 `MenuState` | 用户点击汉堡按钮 / 点击菜单项 | 布尔状态翻转 / 强制关闭 | `nav.open` class 的有无 |
| 卡片动画 `CardAnimator` | 卡片在视口中的位置（IntersectionObserver） | 按卡片序号计算错峰延迟 `index * 0.08s` | 卡片从 `opacity:0; translateY(16px)` 过渡到 `opacity:1; translateY(0)` |
| 文章校验 `validate_post` | 一篇以 dict 表示的文章 | 检查 5 个必填字段、`tags` 类型、`title` 非空 | `True` 或抛出 `ValueError` / `TypeError` |

## 为什么把 JS 逻辑重写一遍

不是为了"用 Python 重写前端"这种炫技，而是三个实际原因：

1. **可测**：浏览器里的 `classList.toggle` 无法在 CI 里断言，等价成 `MenuState.toggle()` 后可以一行断言。
2. **可迁移**：逻辑与 DOM 解耦，将来换成 React、Vue 甚至服务端渲染，状态机不用重写。
3. **可对照**：`core.py` 每个方法上方都贴了它对应的 JS 原文（见 `get_initial_theme`、`register_card` 等处的 docstring），两边行为一旦分叉，读代码就能发现。

## 已知限制

- `index.html` 中有两处图片仍使用本地绝对路径（`file:///D:/niufu/glogo.png`），换台机器打开会显示裂图，应改为仓库内相对路径。
- 文章列表目前是手写在 HTML 里的静态卡片，没有数据源；`filter_posts_by_category` / `filter_posts_by_tag` 已经写好，但还没有接到页面上。
- 没有做真正的语法高亮，`post.html` 里的代码块靠 `--code-bg` 变量渲染成等宽色块。

## 作者

王嵩皓 · 计科 ISEC4 班 · 学号 042540432
