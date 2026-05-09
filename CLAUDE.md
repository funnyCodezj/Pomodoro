# 番茄钟 (Pomodoro Timer) — 项目指南

## 项目概述

番茄钟桌面计时应用，带统计追踪功能。后端使用 FastAPI 提供 Vue 3 SPA 服务，通过 PyWebView 封装为原生桌面窗口（固定 420×700，不可调大小）。生产环境前端编译为静态文件由 FastAPI 托管；开发模式下 Vite 开发服务器和 uvicorn 独立运行。

## 目录结构

```
pomodoro/
├── pomodoro.ico             # 番茄图标（PyInstaller 打包用）
├── requirements.txt         # Python 依赖
├── pomodoro.db              # SQLite 数据库（自动创建，不纳入版本控制）
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用 & API 路由
│   ├── database.py          # SQLAlchemy 引擎、SessionLocal、get_db 依赖注入
│   ├── models.py            # ORM 模型（PomodoroSession, Settings）
│   └── schemas.py           # Pydantic v2 请求/响应模型
└── frontend/
    ├── index.html           # HTML 入口（zh-CN）
    ├── package.json         # Vue 3 + Vite 5
    ├── vite.config.js       # Vite 配置（base: './' 相对路径）
    ├── dist/                # 构建输出（由 FastAPI 托管）
    └── src/
        ├── main.js          # Vue 应用启动
        ├── App.vue          # 根组件：标签页切换、provide 共享状态
        ├── style.css        # 全局 CSS 变量（深色主题）
        ├── utils/
        │   └── api.js       # 基于 fetch 的 API 客户端
        └── components/
            ├── TimerSection.vue    # 番茄钟计时器（SVG 环形进度）
            ├── StatsSection.vue    # 统计面板（周柱状图 + 年度折线图）
            ├── HistorySection.vue  # 历史记录列表
            └── SettingsSheet.vue   # 设置底部弹出面板
```

## 技术栈

| 层次 | 技术 |
|---|---|
| 桌面壳 | PyWebView 4 |
| 后端 | FastAPI + Uvicorn |
| 数据库 | SQLite + SQLAlchemy 2.0 |
| 前端 | Vue 3（Composition API，`<script setup>`） |
| 构建工具 | Vite 5 + @vitejs/plugin-vue |
| HTTP 客户端 | 原生 `fetch`（不使用 axios） |
| 样式 | Scoped CSS + CSS 自定义属性（深色主题） |
| 字体 | Inter（Google Fonts） |

## 后端规范

### 架构
- **分层**：`models.py`（ORM）→ `schemas.py`（Pydantic）→ `main.py`（路由）→ `database.py`（引擎/会话）
- **路由**：函数式视图（不使用类视图），通过 `@app.*` 装饰
- **依赖注入**：数据库会话通过 `Depends(get_db)` 管理
- **端口**：8765（硬编码于 `app.py`）

### API 设计
- 所有路由以 `/api/` 为前缀
- 健康检查：`GET /api/health`
- CRUD 端点：`POST/GET /api/sessions`、`DELETE /api/sessions`、`DELETE /api/sessions/{session_id}`、`GET/PUT /api/settings`、`GET /api/stats`、`GET /api/stats/yearly?year=`
- CORS：全开放（`allow_origins=["*"]`）
- 时间戳：北京时间（UTC+8），ISO 格式（`%Y-%m-%d`）
- 响应模型：Pydantic v2，`from_attributes = True`

### Python 风格
- 4 空格缩进，优先使用单引号
- 所有函数签名使用类型提示
- 私有辅助函数加下划线前缀（如 `_weekday_cn`）
- 时间统一使用 `now_beijing()` 获取北京时间
- 错误日志使用 `print`（当前未使用独立日志模块）

### 数据库
- **模型**：PomodoroSession（id, type, duration, completed_at）、Settings（id, key, value）
- **sessions 表**：type 取值为 `"work"`、`"short_break"` 或 `"long_break"`；duration 单位为秒
- **settings 表**：键值对存储（值存字符串，API 层转 int）
- **默认值**：专注=25min、短休息=5min、长休息=15min、长休息间隔=4
- **连接串**：`sqlite:///pomodoro.db`（相对于项目根目录）
- **建表**：启动时通过 `Base.metadata.create_all(bind=engine)` 自动创建

## 前端规范

### Vue 3 模式
- **始终**使用 `<script setup>` 语法（不使用 Options API）
- **状态管理**：`ref()` 用于本地状态，`inject()`/`provide()` 用于跨组件共享（不使用 Pinia/Vuex）
- **Props**：使用 `defineProps`，事件通过 `defineEmits` 声明
- **标签页**：通过 `v-show` 配合 `activeTab` ref 控制（不使用 Vue Router）
- **生命周期**：`onMounted`、`onUnmounted`
- **异步**：`async/await` + try/catch

### 样式
- **深色主题**：通过 `:root` 的 CSS 自定义属性定义（`--bg-*`、`--text-*`、`--work`、`--break` 等）
- **Scoped 样式**：每个组件均使用 `<style scoped>`
- **类命名**：kebab-case（如 `.timer-ring-wrap`、`.session-tag`）
- **动画**：`fadeIn`（0.4s）、`slideUp`（0.3s）、hover/active 状态 CSS 过渡
- **全局重置**：`style.css` 中 `* { margin: 0; padding: 0; box-sizing: border-box; }`
- **按钮点击态**：`:active` 时 `transform: scale(0.96)`
- **字体栈**：`'Inter', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif`

### JavaScript 风格
- 2 空格缩进，单引号，无分号
- 不使用 TypeScript（纯 JavaScript）
- API 客户端：普通对象模式（`export const api = { ... }`），共用 `request()` 封装
- 错误处理：`console.error`（简洁风格）

### 组件通信
- 根组件 `App.vue` 通过 `provide` 提供共享状态：`settings`、`stats`、`sessions`、`refreshStats`
- 子组件通过 `inject()` 获取所需状态
- `refreshStats()` 内部使用 `Promise.all` 同时获取统计和会话数据

## 开发工作流

### 开发模式启动
```bash
# 终端 1 — 后端
cd pomodoro && pip install -r requirements.txt && uvicorn backend.main:app --reload --port 8765

# 终端 2 — 前端
cd pomodoro/frontend && npm install && npm run dev
```

### 生产构建
```bash
cd pomodoro/frontend && npm run build
# 然后执行：python app.py  （前端由 FastAPI 从 dist/ 目录提供服务）
```

### 打包 Windows exe
```bash
cd pomodoro/frontend && npm run build          # 先构建前端
cd pomodoro && pyinstaller --name "Pomodoro" --icon pomodoro.ico --onedir --windowed --add-data "frontend/dist;frontend/dist" --hidden-import webview --hidden-import webview.platforms.winforms --hidden-import uvicorn --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto --hidden-import uvicorn.protocols.http.auto app.py
# 输出：dist/Pomodoro/Pomodoro.exe（39MB，含 _internal/ 依赖）
```

注意：
- `--onedir` 模式，数据库 `pomodoro.db` 生成在 exe 同级目录（持久化）
- `sys._MEIPASS` 指向 `_internal/`（前端静态文件位置）
- `os.path.dirname(sys.executable)` 指向 exe 目录（数据库位置）

### 关键依赖
- Python：fastapi、uvicorn、sqlalchemy、pywebview
- Node：vue、vite、@vitejs/plugin-vue

## 命名与编码规则

### 文件与目录
- Python 文件：`snake_case.py`
- Vue 文件：`PascalCase.vue`
- JS 工具文件：`camelCase.js`
- 目录：小写、单数形式

### API 客户端方法
- `createSession(type, duration)` — POST /api/sessions
- `getSessions(limit)` — GET /api/sessions
- `getStats()` — GET /api/stats
- `getYearlyStats(year)` — GET /api/stats/yearly?year=
- `getSettings()` — GET /api/settings
- `updateSettings(data)` — PUT /api/settings
- `clearSessions()` — DELETE /api/sessions
- `deleteSession(id)` — DELETE /api/sessions/{id}

### 数据键名约定
- 设置项键名使用**蛇形命名法（snake_case）**：`work_duration`、`short_break`、`long_break`、`cycles_before_long`
- 后端 API 返回/接收 snake_case 键名
- 前端组件中访问设置值时必须使用 snake_case（与 API 一致，不做键名转换）

### 组件 Props 与事件
- Props：模板中使用 camelCase
- Emits：kebab-case 或 camelCase（Vue 3 自动规范化）
- Provide/inject 键名：camelCase 字符串

## 环境与工具

### 包管理器
- Python：pip（requirements.txt，不使用 Pipfile/poetry）
- Node：npm（package-lock.json 纳入版本控制）

### 配置
- 项目级 Claude 配置：`.claude/settings.local.json`
- 已配置 npm/pip 操作权限

### 重要路径
- 数据库：`pomodoro/pomodoro.db`（自动创建，避免手动编辑）
- 前端构建输出：`pomodoro/frontend/dist/`（前端变更后需重新构建）
- Python 路径：`app.py` 在运行时通过 `sys.path` 插入项目根目录

## 约束 / 避免事项

- 不要引入 Vue Router、Pinia、TypeScript 或 axios — 项目使用更简洁的模式
- 不要修改窗口尺寸（420×700）或可调大小属性
- 不要删除 `vite.config.js` 中的 `base: './'`（PyWebView 兼容性要求）
- 不要将函数式路由改为类视图
- 除非错误处理复杂度显著增长，不要添加独立的 Python 日志模块
- 数据库迁移采用手动方式（SQLite，不使用 Alembic）

## 文档同步规则（强制）

- **每次对项目的任何修改**（代码、依赖、目录结构、配置、工作流）必须同步更新 `CLAUDE.md` 的对应章节
- 新增文件/目录 → 更新「目录结构」
- 新增依赖 → 更新「技术栈」或「关键依赖」
- 变更工作流/命令 → 更新「开发工作流」
- 新增约定/规范 → 更新对应规范章节

## 自测规则（强制）

每次修改代码后必须在提交前执行自测：

### 后端修改自测
```bash
# 1. 启动后端
cd pomodoro && uvicorn backend.main:app --reload --port 8765

# 2. 测试健康检查和 API
curl -s http://127.0.0.1:8765/api/health
curl -s http://127.0.0.1:8765/api/settings | python -m json.tool

# 3. 创建/查询测试数据
curl -s -X POST http://127.0.0.1:8765/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"type":"work","duration":60}'
curl -s http://127.0.0.1:8765/api/sessions?limit=5
```

### 前端修改自测
```bash
# 1. 构建验证（确保无编译错误）
cd pomodoro/frontend && npm run build

# 2. 开发服务器验证（人工打开浏览器检查）
npm run dev
# 打开 http://localhost:5173 检查 UI
```

### Web 访问（web-access skill）

需要 Chrome 开启远程调试端口（9222）才能使用浏览器 CDP 模式。
项目已配置 PreToolUse hook（`.claude/settings.local.json`），在执行 web-access 相关 curl 命令时自动检测并启动 Chrome：
```bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --no-first-run
```

### 涉及状态/逻辑修改 — 端到端浏览器测试
使用 Playwright 编写自动化测试脚本，覆盖：
- 状态变化路径（如：专注→短休息→专注→长休息）
- 设置持久化（修改→刷新→验证值保留）
- 临界条件（空状态、边界值、极端输入）

```bash
# 前置条件：后端 + 前端 dev server 均已启动
cd pomodoro && node test_<name>.mjs
```



