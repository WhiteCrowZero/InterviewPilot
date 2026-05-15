# InterviewPilot

基于 FastAPI 的智能面试复习系统。

## 当前阶段

已完成阶段 0 的基础骨架：

- `src/` 混合式分层结构（`core / db / api / modules`）
- FastAPI 应用入口与路由聚合
- 配置文件与全局占位模块
- 测试目录与健康检查示例
- Docker / Alembic 基础目录

## 快速启动

```bash
uv sync
uv run uvicorn src.main:app --reload
```

访问地址：

- `http://127.0.0.1:8000/api/v1/health`

## 后续阶段建议

1. 阶段 1：补全统一响应、异常处理、中间件、日志。
2. 阶段 2：接入 SQLAlchemy、用户表、JWT 鉴权。
3. 阶段 3：实现题库、错题本、笔记核心业务。
