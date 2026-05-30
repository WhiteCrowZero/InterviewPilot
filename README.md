# InterviewPilot

基于 FastAPI 的智能面试复习系统。这个版本是“完整学习版”：它不是为了堆功能，而是把你目前需要补的工程薄弱点串成一条清晰主线。

## 当前已覆盖的能力

- FastAPI 路由拆分：`main -> api_router -> endpoint -> service -> repository`
- SQLAlchemy 异步 ORM：用户、题目、笔记、错题记录
- JWT 登录鉴权：注册、登录、`/users/me`、当前用户依赖
- 用户数据隔离：`current_user.id` 贯穿 questions / notes / reviews
- Redis 缓存：dashboard summary 使用 Cache Aside 模式
- 消息队列：写操作后发布领域事件
- WebSocket：后台 worker 消费事件并推送实时通知
- 测试：接口级测试、缓存失效测试、消息队列测试、WebSocket 测试
- 工程质量：ruff / pyright / pytest 可作为日常检查三件套

## 技术栈

- FastAPI
- SQLAlchemy async
- SQLite / aiosqlite
- Alembic
- Pydantic v2
- PyJWT
- pwdlib[argon2]
- Redis Python client
- pytest + TestClient
- ruff + pyright

## 项目结构

```text
src/interview_pilot/
  main.py                         # 应用入口，lifespan 管理缓存、队列、worker
  api/
    deps.py                       # Session / current_user / cache / queue 依赖
    v1/endpoints/                 # HTTP 和 WebSocket 入口
  core/
    cache.py                      # Redis/内存缓存抽象
    message_queue.py              # Redis/内存消息队列抽象
    security.py                   # 密码哈希与 JWT
  db/
    base.py                       # SQLAlchemy Base
    models.py                     # 统一导入所有 ORM 模型
    session.py                    # engine / SessionLocal / get_db_session
  modules/
    auth/                         # 注册登录
    questions/                    # 题库 CRUD
    notes/                        # 笔记 CRUD
    reviews/                      # 错题记录 CRUD
    dashboard/                    # 聚合统计 + Redis 缓存
  realtime/
    manager.py                    # WebSocket 在线连接管理
  workers/
    event_worker.py               # 消费消息队列，推送 WebSocket 通知
```

## 快速启动

```bash
uv sync
uv run uvicorn interview_pilot.main:app --reload
```

访问：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/v1/health
```

## 测试与质量检查

```bash
uv run pytest -q
uv run ruff check .
uv run pyright
```

当前参考结果：

```text
21 passed
ruff: All checks passed
pyright: 0 errors
```

## Redis / 消息队列 / WebSocket 学习主线

### 1. Redis 缓存：Dashboard Summary

接口：

```text
GET /api/v1/dashboard/summary
```

流程：

```text
请求 dashboard
  ↓
service 先查 cache
  ↓
缓存命中：直接返回
缓存未命中：查数据库 COUNT / GROUP BY
  ↓
写回 cache
  ↓
返回响应
```

写操作后会删除缓存：

```text
create/update/delete question/note/review
  ↓
数据库写入成功
  ↓
invalidate_dashboard_cache(user_id)
```

学习重点：这是 Cache Aside 模式。Redis 不是数据库真相来源，数据库才是最终事实。

### 2. 消息队列：领域事件

写操作成功后会发布事件：

```text
question.created
question.updated
question.deleted
note.created
review.created
...
```

流程：

```text
service 完成数据库写入
  ↓
message_queue.publish(DomainEvent)
  ↓
后台 worker 消费事件
  ↓
推送 WebSocket 通知
```

学习重点：主流程和副作用解耦。接口不需要直接关心有没有用户在线，也不需要直接处理 WebSocket 推送。

### 3. WebSocket：当前用户实时通知

连接地址：

```text
ws://127.0.0.1:8000/api/v1/ws/notifications?token=<access_token>
```

流程：

```text
WebSocket 握手
  ↓
从 query token 解码 JWT
  ↓
查数据库得到当前用户
  ↓
加入 websocket_manager
  ↓
worker 消费到事件后推送给该 user_id 的所有在线连接
```

学习重点：HTTP 是请求响应，WebSocket 是长连接。后端必须保存连接关系，才能主动推送。

## 本项目特意保留的学习注释

你可以重点读这些文件里的注释：

```text
src/interview_pilot/core/cache.py
src/interview_pilot/core/message_queue.py
src/interview_pilot/modules/dashboard/service.py
src/interview_pilot/realtime/manager.py
src/interview_pilot/workers/event_worker.py
src/interview_pilot/api/v1/endpoints/ws.py
```

这些注释专门围绕你的薄弱点写：缓存失效、消息队列解耦、WebSocket 连接管理、测试替身、权限边界。

## Docker Compose 启动 Redis 版本

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Compose 中 API 会使用：

```text
CACHE_BACKEND=redis
MESSAGE_QUEUE_BACKEND=redis
REDIS_URL=redis://redis:6379/0
```

本地不启动 Redis 时，`.env.example` 默认使用 `memory`，方便你先看代码和跑测试。

## 建议学习顺序

1. 先复习主链路：`endpoint -> service -> repository -> db`
2. 看 `dashboard/service.py`，理解 Redis Cache Aside
3. 看 `core/cache.py`，理解为什么抽象缓存接口
4. 看 `core/message_queue.py`，理解事件对象和队列接口
5. 看 `questions/service.py`，理解写库后如何删除缓存、发布事件
6. 看 `workers/event_worker.py`，理解后台消费者
7. 看 `realtime/manager.py` 和 `ws.py`，理解 WebSocket 连接管理
8. 看 `tests/unit/test_cache_queue_websocket.py`，理解如何测试缓存、队列、WebSocket

## 面试可讲亮点

- 用户私有数据全部通过 `current_user.id` 做权限边界
- dashboard summary 使用 Redis 缓存，写操作后按用户删除缓存
- 业务事件通过消息队列发布，后台 worker 统一处理通知推送
- WebSocket 只推送给当前用户，不做全局广播，避免越权通知
- 测试环境用内存缓存和内存消息队列替代 Redis，保证测试稳定可重复
- 项目没有把 Redis、队列、WebSocket 硬编码进业务层，而是通过依赖和抽象层隔离
