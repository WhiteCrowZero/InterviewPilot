from tests.conftest import create_test_client


def test_create_and_list_questions() -> None:
    client = create_test_client()

    payload = {
        "title": "什么是事务？",
        "answer": "事务是一组要么全部成功要么全部失败的操作。",
        "category": "database",
        "difficulty": 2,
        "tags": ["sql", "transaction"],
    }

    create_response = client.post("/api/v1/questions", json=payload)

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == 1
    assert created["title"] == payload["title"]
    assert created["tags"] == payload["tags"]

    list_response = client.get("/api/v1/questions")

    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]
    assert listed[0]["title"] == payload["title"]


def test_category_summary_report_uses_raw_sql() -> None:
    client = create_test_client()

    payloads = [
        {
            "title": "事务隔离级别有哪些？",
            "answer": "读未提交、读已提交、可重复读、串行化。",
            "category": "database",
            "difficulty": 4,
            "tags": ["sql"],
        },
        {
            "title": "什么是索引覆盖？",
            "answer": "查询需要的列都能直接从索引中拿到，减少回表。",
            "category": "database",
            "difficulty": 3,
            "tags": ["sql", "index"],
        },
        {
            "title": "FastAPI 的 Depends 是做什么的？",
            "answer": "用于声明依赖，由框架在请求处理时解析和注入。",
            "category": "backend",
            "difficulty": 2,
            "tags": ["fastapi"],
        },
    ]

    for payload in payloads:
        response = client.post("/api/v1/questions", json=payload)
        assert response.status_code == 201

    report_response = client.get("/api/v1/questions/reports/category-summary")

    assert report_response.status_code == 200
    rows = report_response.json()
    assert len(rows) == 2

    database_row = rows[0]
    assert database_row["category"] == "database"
    assert database_row["question_count"] == 2
    assert database_row["hard_question_count"] == 1
    assert database_row["volume_rank"] == 1

    backend_row = rows[1]
    assert backend_row["category"] == "backend"
    assert backend_row["question_count"] == 1
    assert backend_row["volume_rank"] == 2
