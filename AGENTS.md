# Python Backend Project Agent Rules

## 1. Project Principles

> Product goals come first. Technical choices must serve real project needs.

Treat this project as a small-to-medium Python backend project by default. Prioritize:

- Simplicity and clarity
- Runnable and maintainable code
- Gradual extensibility

Do not over-engineer or introduce premature abstractions.

Confirm with the user before making any important design decision, complex implementation, new dependency, or new
architecture.

---

## 2. Development Workflow

Follow MVP-first and small-step iteration:

1. Build the minimum runnable version first.
2. Then create the minimum project structure.
3. Improve core modules step by step.
4. Add non-core features only after the core flow is stable.

Handle only one clear target at a time, such as one feature, one bug, one API, or one small module improvement.

Do not directly perform large-scale changes, full rewrites, or multi-module refactors.

If the request is too large, first split it into smaller tasks or create a concrete plan. Write the plan into a Plan
document, clarify requirements with the user, and wait for user confirmation before editing code.

---

## 3. Tools and Environment

Development tools:

- Dependency management: `uv`
- Testing: `pytest`

Use uv-native commands by default, such as:

```bash
uv add
uv remove
uv run
````

Do not use `uv pip` by default unless the user explicitly asks for it.

---

## 4. Verification and Testing

Runtime code changes must include verification.

Do not add tests blindly or create excessive tests.

New tests should cover only the most important core paths. Confirm with the user before adding more tests.

Watch for test timeouts. If tests hang for too long, stop waiting, explain where they got stuck, and suggest the next
debugging step.

---

## 5. Special Rules

### Git

* Do not perform any Git write operations.
* Only Git read operations are allowed.
* You may suggest branch names and commit messages, but must not execute them.

### Coding Style

* Use clear and accurate type annotations in Python code whenever possible.
* Avoid `Any` unless the type cannot be expressed accurately.
* Add this to new Python files by default:

```python
from __future__ import annotations
```

### WSL and Windows

The development environment is in WSL and is isolated from the actual Windows code environment.

- Current directory: `~/projects/InterviewPilot/`
- Windows directory: `/mnt/d/ComputerScience/Python/temp/InterviewPilot/`

---

## 6. Project Structure

This is the main structure of the current project, which will be continuously iterated as the project develops. Every
major structural adjustment needs to be updated in a timely manner:

```txt
InterviewPilot/
├── src/
│   └── interview_pilot/
│       ├── main.py                         # 项目入口：创建 FastAPI app，注册 API 总路由
│       ├── core/
│       │   ├── config.py                    # 项目配置：项目名、版本、API 前缀、数据库地址等
│       │   └── security.py                  # 安全相关：密码哈希、JWT 生成与解析
│       ├── api/
│       │   ├── deps.py                      # 公共依赖：数据库 session、当前登录用户、权限校验等
│       │   └── v1/
│       │       ├── router.py                # v1 总路由：聚合模块
│       │       └── endpoints/
│       │           ├── health.py            # 健康检查接口
│       │           └── xxx.py               # xxx模块接口
│       ├── db/
│       │   ├── base.py                      # SQLAlchemy Base；统一收集 ORM 模型 metadata
│       │   ├── session.py                   # 数据库 engine、SessionLocal、get_db_session
│       │   └── models.py                    # 统一导入所有 ORM 模型，方便 Alembic 识别表结构
│       └── modules/
│           ├── xxx/
│           └── xxx/
│               ├── models.py            # 数据库ORM模型
│               ├── schemas.py           # JSON序列化模型
│               ├── repository.py        # 数据库SQL操作
│               └── service.py           # 业务逻辑
├── tests/
│   ├── conftest.py                      # 测试配置：测试数据库、依赖覆盖、测试客户端
│   └── test_xxx.py                      # xxx 模块测试
├── alembic/
│   ├── env.py                           # Alembic 配置：读取 Base.metadata，生成/执行迁移
│   └── versions/
├── deploy/
│   ├── Dockerfile                       # 项目镜像构建
│   └── docker-compose.yml               # 本地部署：API、数据库、Redis 等
├── pyproject.toml                       # 项目依赖、ruff/pytest 等工具配置
├── alembic.ini                          # Alembic 主配置文件
├── .env.example                         # 环境变量示例
└── README.md                            # 项目介绍、启动方式、接口说明、架构说明
```
