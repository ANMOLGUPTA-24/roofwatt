import json
import os
import sqlite3
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Literal
from uuid import uuid4

import boto3
import jwt
from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from mangum import Mangum
from pydantic import BaseModel, Field

app = FastAPI(title="LeakLoop")
logger = Logger(service="leakloop")
JWKS_CLIENTS: dict[str, jwt.PyJWKClient] = {}


class LeakType(str, Enum):
    pipe = "pipe"
    tap = "tap"
    overflow = "overflow"


class FlowTest(BaseModel):
    container_ml: float = Field(ge=10, le=20_000)
    fill_seconds: float = Field(ge=0.5, le=3_600)


class PostCheck(BaseModel):
    collected_ml: float = Field(ge=0, le=20_000)
    observation_seconds: float = Field(ge=5, le=3_600)


class LeakCreate(BaseModel):
    kind: LeakType
    location: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=8, max_length=500)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    estimated_lpd: float | None = Field(default=None, ge=0, le=1_000_000)
    flow_test: FlowTest | None = None


class LeakAction(BaseModel):
    action: Literal["acknowledged", "checked"]
    note: str = Field(min_length=4, max_length=300)
    post_check: PostCheck | None = None
    repair_photo_key: str | None = Field(default=None, max_length=160)


class UploadRequest(BaseModel):
    context: Literal["repair"]
    content_type: Literal["image/jpeg", "image/png", "image/webp"]


def _flow_lpd(test: FlowTest | dict) -> float:
    data = test.model_dump() if isinstance(test, FlowTest) else test
    volume = data.get("container_ml", data.get("collected_ml"))
    seconds = data.get("fill_seconds", data.get("observation_seconds"))
    return round((float(volume) / 1000 / float(seconds)) * 86_400, 1)


def _table():
    name = os.environ.get("LEAKS_TABLE")
    return boto3.resource("dynamodb").Table(name) if name else None


def _local_connection() -> sqlite3.Connection:
    path = Path(os.environ.get("LEAKLOOP_DB", Path(__file__).resolve().parents[2] / "data" / "leakloop.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE IF NOT EXISTS issues (id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL)")
    return connection


def _photos():
    name = os.environ.get("EVIDENCE_BUCKET")
    return (boto3.client("s3") if name else None), name


def _is_valid_photo_key(key: str | None, context: str) -> bool:
    return bool(key and key.startswith(f"evidence/{context}s/") and len(key) <= 160)


def _present_issue(issue: dict) -> dict:
    present = dict(issue)
    client, bucket = _photos()
    key = present.pop("repair_photo_key", None)
    if key and bucket:
        present["repair_photo_url"] = client.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=900)
    return present


def _all_issues() -> list[dict]:
    table = _table()
    if table:
        return table.scan().get("Items", [])
    with _local_connection() as connection:
        return [json.loads(row[0]) for row in connection.execute("SELECT payload FROM issues")]


def _save_issue(issue: dict, expected_status: str | None = None) -> None:
    table = _table()
    if table:
        condition = Attr("id").not_exists() if expected_status is None else Attr("status").eq(expected_status)
        try:
            table.put_item(Item=issue, ConditionExpression=condition)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise HTTPException(409, "This report changed. Refresh the board and try again.") from exc
            raise
        return
    with _local_connection() as connection:
        existing = connection.execute("SELECT payload FROM issues WHERE id = ?", (issue["id"],)).fetchone()
        if expected_status is None and existing:
            raise HTTPException(409, "A report with this id already exists")
        if expected_status is not None and (not existing or json.loads(existing[0])["status"] != expected_status):
            raise HTTPException(409, "This report changed. Refresh the board and try again.")
        connection.execute("INSERT OR REPLACE INTO issues(id, payload, created_at) VALUES (?, ?, ?)", (issue["id"], json.dumps(issue), issue["created_at"]))


def _summary(issues: list[dict]) -> dict:
    active = [item for item in issues if item["status"] != "repaired"]
    repaired = [item for item in issues if item["status"] == "repaired"]
    return {
        "open_reports": len(active),
        "repair_count": len(repaired),
        "measured_active_lpd": round(sum(float(item.get("baseline_lpd") or 0) for item in active)),
        "measured_lpd_stopped": round(sum(float(item.get("stopped_lpd") or 0) for item in repaired)),
    }


def _maintenance_identity(authorization: str | None) -> str:
    user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
    if not user_pool_id:
        return "local-demo"
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in with a maintenance account to update this report.")
    region, token = os.environ["AWS_REGION"], authorization.removeprefix("Bearer ")
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    try:
        client = JWKS_CLIENTS.setdefault(issuer, jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json"))
        claims = jwt.decode(token, client.get_signing_key_from_jwt(token).key, algorithms=["RS256"], issuer=issuer, options={"verify_aud": False})
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Your maintenance session is invalid or expired. Sign in again.") from exc
    if claims.get("token_use") != "access" or claims.get("client_id") != os.environ.get("COGNITO_CLIENT_ID"):
        raise HTTPException(401, "This is not a valid maintenance session.")
    if "maintenance" not in claims.get("cognito:groups", []):
        raise HTTPException(403, "This account is not in the maintenance team.")
    return str(claims.get("username", "maintenance"))


def require_maintenance(authorization: str | None = Header(default=None)) -> str:
    return _maintenance_identity(authorization)


def _notify(event: str, issue: dict) -> None:
    topic = os.environ.get("NOTIFICATION_TOPIC_ARN")
    if not topic:
        return
    try:
        boto3.client("sns").publish(TopicArn=topic, Subject="LeakLoop maintenance update", Message=f"LeakLoop {event}: {issue['kind']} at {issue['location']} is now {issue['status']}.")
    except ClientError:
        logger.exception("notification_failed", extra={"issue_id": issue["id"], "event": event})


@app.get("/health")
def health():
    return {"ok": True, "service": "LeakLoop", "local_storage": _table() is None}


@app.get("/config")
def config():
    hosted_ui = os.environ.get("COGNITO_HOSTED_UI")
    return {"maintenance_auth": bool(hosted_ui), "hosted_ui": hosted_ui, "client_id": os.environ.get("COGNITO_CLIENT_ID"), "callback_url": os.environ.get("APP_URL"), "evidence_uploads": bool(os.environ.get("EVIDENCE_BUCKET"))}


@app.get("/issues")
def list_issues():
    issues = sorted(_all_issues(), key=lambda item: item["created_at"], reverse=True)
    return {"issues": [_present_issue(issue) for issue in issues], "summary": _summary(issues), "persistent": True}


@app.post("/uploads/presign")
def presign_upload(req: UploadRequest, authorization: str | None = Header(default=None)):
    _maintenance_identity(authorization)
    client, bucket = _photos()
    if not bucket:
        raise HTTPException(503, "Photo evidence is available after AWS deployment.")
    extension = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[req.content_type]
    key = f"evidence/{req.context}s/{uuid4()}.{extension}"
    return {"key": key, "upload_url": client.generate_presigned_url("put_object", Params={"Bucket": bucket, "Key": key, "ContentType": req.content_type}, ExpiresIn=300)}


@app.post("/issues", status_code=201)
def report_issue(req: LeakCreate):
    now = datetime.now(UTC).isoformat()
    baseline_lpd = _flow_lpd(req.flow_test) if req.flow_test else req.estimated_lpd
    source = "container test" if req.flow_test else ("manual estimate" if req.estimated_lpd is not None else "not measured")
    issue = {
        "id": str(uuid4()), "kind": req.kind.value, "location": req.location.strip(), "description": req.description.strip(),
        "lat": str(req.lat), "lon": str(req.lon), "baseline_lpd": str(baseline_lpd) if baseline_lpd is not None else None,
        "flow_test": req.flow_test.model_dump() if req.flow_test else None, "measurement_source": source,
        "status": "reported", "created_at": now, "timeline": [{"status": "reported", "note": f"Community report created ({source})", "at": now}],
    }
    _save_issue(issue)
    logger.info("leak_reported", extra={"issue_id": issue["id"], "kind": issue["kind"], "measurement_source": source})
    _notify("new report", issue)
    return {"issue": _present_issue(issue), "persistent": True}


@app.post("/issues/{issue_id}/actions")
def update_issue(issue_id: str, req: LeakAction, maintenance_user: str = Depends(require_maintenance)):
    if req.repair_photo_key and not _is_valid_photo_key(req.repair_photo_key, "repair"):
        raise HTTPException(400, "Invalid repair evidence reference")
    issue = next((item for item in _all_issues() if item["id"] == issue_id), None)
    if not issue:
        raise HTTPException(404, "Report not found")
    if issue["status"] == "reported" and req.action != "acknowledged":
        raise HTTPException(409, "A report must be acknowledged before its repair check.")
    if issue["status"] != "acknowledged" and req.action == "checked":
        raise HTTPException(409, "Only acknowledged reports can receive a repair check.")
    if req.action == "checked" and not req.post_check:
        raise HTTPException(400, "Run the post-repair container check before closing this report.")
    previous_status, now = issue["status"], datetime.now(UTC).isoformat()
    if req.action == "acknowledged":
        issue["status"] = "acknowledged"
    else:
        post_lpd = _flow_lpd(req.post_check)
        issue["post_check"] = req.post_check.model_dump()
        issue["post_lpd"] = str(post_lpd)
        issue["stopped_lpd"] = str(max(float(issue.get("baseline_lpd") or 0) - post_lpd, 0))
        issue["repair_photo_key"] = req.repair_photo_key
        issue["status"] = "repaired" if post_lpd == 0 else "follow_up"
    issue["updated_at"] = now
    issue.setdefault("timeline", []).append({"status": issue["status"], "note": req.note.strip(), "at": now, "actor": "maintenance"})
    _save_issue(issue, expected_status=previous_status)
    logger.info("leak_status_changed", extra={"issue_id": issue_id, "status": issue["status"], "maintenance_user": maintenance_user})
    _notify(req.action, issue)
    return {"issue": _present_issue(issue)}


@app.get("/issues/{issue_id}")
def get_issue(issue_id: str):
    issue = next((item for item in _all_issues() if item["id"] == issue_id), None)
    if not issue:
        raise HTTPException(404, "Report not found")
    return {"issue": _present_issue(issue)}


handler = Mangum(app)
FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
