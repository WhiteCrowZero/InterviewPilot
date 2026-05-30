# InterviewPilot 测试目录说明

这个目录按“三层”组织：

```text
tests/
  api/          # API 层测试：像真实用户一样请求接口，验证状态码、响应体、权限边界
  integration/  # 集成测试：验证 HTTP、MQ、worker、WebSocket 等组件能协作
  unit/         # 单元测试：只测一个小组件，例如缓存、消息队列、安全工具函数
  conftest.py   # pytest fixture：创建测试数据库、测试客户端、内存缓存、内存队列
  helpers.py    # 测试辅助函数：注册、登录、创建题目、创建笔记、创建复盘
```

## 推荐运行命令

```bash
uv run pytest -q
uv run pytest tests/api -q
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run pytest tests/api/test_questions_api.py -q
```

## 当前 MVP 测试重点

1. 接口是否能跑通。
2. 登录鉴权是否生效。
3. 用户只能访问自己的数据。
4. 核心 CRUD 是否正常。
5. 写操作是否发布领域事件。
6. Dashboard 缓存是否会在写操作后失效。
7. WebSocket 是否能鉴权、连接和收到后台通知。

## 暂时不做的事情

1. 不测真实 Redis 服务，当前使用 MemoryCacheBackend。
2. 不做复杂压测。
3. 不追求 100% 覆盖率。
4. 不测试所有 Pydantic 422 细节，只测关键输入边界。
5. 不实现真正的 MQ ack/retry/DLQ 测试，因为当前业务代码还没有这些能力。
