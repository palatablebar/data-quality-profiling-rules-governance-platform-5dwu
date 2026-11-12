"""待修正清单（纠错台账）的跨批次结转。

每个规则批次执行完都会同步一次这本台账：

* 命中行按 ``(rule_id, business_key, key_occurrence)`` 归并 —— 同一业务行在
  同一规则下永远只有一条清单记录，修正版重复执行不会新增问题（幂等）；
* 本次仍命中的 open 条目保持待修正，只刷新行号/观测值/最近批次（继续处理）；
* 之前 open、本次其规则已执行但未再命中的条目转 fixed（已修好关闭）；
* 曾经 fixed、后续批次又命中的条目重新打开（回归），不产生第二条记录。

数量对账：``dataset.row_count = 可用记录数 + 清单内去重业务行数``。
业务键重复的行靠 key_occurrence 区分，因此每个物理行恰好算一次。
"""
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.constants.correction_status import CORRECTION_STATUS_LABELS, CorrectionStatus
from app.models import CorrectionItem, Dataset, QualityRule, RuleRun
from app.utils.logger import log_event

ROW_FALLBACK_PREFIX = "row#"
OBSERVED_LIMIT = 2000


def business_keys_for_frame(df: pd.DataFrame, key_column: str | None) -> dict[int, tuple[str, int]]:
    """把每个物理行映射到稳定的 (business_key, key_occurrence) 台账身份。

    key_occurrence 是该业务键在文件内的第几次出现（1 起）：业务键唯一的行
    恒为 1；重复键（如 unique 规则命中的重复账号）各占各的序号，整份重传后
    只要相对顺序不变身份就稳定，同一业务行不会被重复计算。
    """
    if key_column and key_column in df.columns:
        raw = df[key_column]
        values = {
            idx: ("" if pd.isna(value) else str(value).strip()) or f"{ROW_FALLBACK_PREFIX}{idx}"
            for idx, value in raw.items()
        }
    else:
        values = {idx: f"{ROW_FALLBACK_PREFIX}{idx}" for idx in df.index}
    seen: dict[str, int] = {}
    keys: dict[int, tuple[str, int]] = {}
    for idx in df.index:
        value = values[idx]
        seen[value] = seen.get(value, 0) + 1
        keys[idx] = (value, seen[value])
    return keys


def _observed_at(df: pd.DataFrame, row_index: int, column: str) -> str:
    try:
        value = df.at[row_index, column]
    except KeyError:  # pragma: no cover - 防御：行号一定来自同一个 df
        return ""
    text = "" if pd.isna(value) else str(value)
    return text[:OBSERVED_LIMIT]


def sync_after_run(
    db: Session,
    dataset: Dataset,
    run: RuleRun,
    rules: list[QualityRule],
    expected_by_rule: dict[int, str],
    df: pd.DataFrame,
    violations_by_rule: dict[int, set[int]],
) -> dict:
    """按本批次违规集合结转台账，返回并落盘 run.correction_json 快照。

    只处理 violations_by_rule 里真实执行成功的规则（执行失败的规则不在内，
    其 open 条目保持原状，不会被误关）。
    """
    rules_by_id = {rule.id: rule for rule in rules}
    scanned_rule_ids = set(violations_by_rule.keys())
    key_map = business_keys_for_frame(df, dataset.business_key_column)

    items = db.query(CorrectionItem).filter(CorrectionItem.dataset_id == dataset.id).all()
    open_by_identity: dict[tuple, CorrectionItem] = {}
    fixed_by_identity: dict[tuple, CorrectionItem] = {}
    for item in items:
        identity = (item.rule_id, item.business_key, item.key_occurrence)
        if item.status == CorrectionStatus.OPEN.value:
            open_by_identity[identity] = item
        else:
            fixed_by_identity[identity] = item

    created = 0
    still_open = 0
    reopened = 0
    for rule_id, violated_rows in violations_by_rule.items():
        rule = rules_by_id.get(rule_id)
        if rule is None:
            continue
        expected = (expected_by_rule.get(rule_id) or "")[:OBSERVED_LIMIT]
        for row_index in sorted(violated_rows):
            business_key, occurrence = key_map.get(row_index, (f"{ROW_FALLBACK_PREFIX}{row_index}", 1))
            identity = (rule_id, business_key, occurrence)
            observed = _observed_at(df, row_index, rule.column_name)

            item = open_by_identity.pop(identity, None)
            if item is not None:
                # 仍未改好：继续处理，刷新到最新文件里的位置与观测值
                item.row_index = row_index
                item.observed_value = observed
                item.expected_expr = expected
                item.last_seen_run_id = run.id
                still_open += 1
                continue
            item = fixed_by_identity.pop(identity, None)
            if item is not None:
                # 曾经修好又复发：重新打开原条目，不新增记录
                item.status = CorrectionStatus.OPEN.value
                item.row_index = row_index
                item.observed_value = observed
                item.expected_expr = expected
                item.last_seen_run_id = run.id
                item.fixed_run_id = None
                item.fixed_at = None
                reopened += 1
                continue
            db.add(
                CorrectionItem(
                    dataset_id=dataset.id,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    column_name=rule.column_name,
                    severity=rule.severity,
                    business_key=business_key,
                    key_occurrence=occurrence,
                    row_index=row_index,
                    first_row_index=row_index,
                    observed_value=observed,
                    expected_expr=expected,
                    status=CorrectionStatus.OPEN.value,
                    first_seen_run_id=run.id,
                    last_seen_run_id=run.id,
                )
            )
            created += 1

    fixed = 0
    now = datetime.now()
    for item in open_by_identity.values():
        if item.rule_id not in scanned_rule_ids:
            continue  # 该规则本次没执行成功，条目不结转
        # 本次未再命中：已修好，关闭
        item.status = CorrectionStatus.FIXED.value
        item.fixed_run_id = run.id
        item.fixed_at = now
        fixed += 1
    db.flush()

    open_items = [
        item
        for item in db.query(CorrectionItem).filter(
            CorrectionItem.dataset_id == dataset.id,
            CorrectionItem.status == CorrectionStatus.OPEN.value,
        ).all()
    ]
    open_bad_rows = {(item.business_key, item.key_occurrence) for item in open_items}
    total_rows = int(run.rows_scanned or 0)
    usable_rows = max(0, total_rows - len(open_bad_rows))
    summary = {
        "created": created,
        "still_open": still_open,
        "reopened": reopened,
        "fixed": fixed,
        "open_entries": len(open_items),
        "open_bad_rows": len(open_bad_rows),
        "usable_rows": usable_rows,
        "total_rows": total_rows,
        "balanced": usable_rows + len(open_bad_rows) == total_rows,
        "business_key_column": dataset.business_key_column,
    }
    run.correction_json = summary
    log_event(
        "CORRECTION_SYNCED",
        run_id=run.id,
        dataset_id=dataset.id,
        created=created,
        still_open=still_open,
        reopened=reopened,
        fixed=fixed,
        open_entries=len(open_items),
    )
    return summary


def list_items(
    db: Session,
    dataset_id: int,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    from app.utils.pagination import paginate_query

    query = db.query(CorrectionItem).filter(CorrectionItem.dataset_id == dataset_id)
    if status:
        query = query.filter(CorrectionItem.status == status)
    return paginate_query(query.order_by(CorrectionItem.id.asc()), page, page_size)


def reconciliation(db: Session, dataset: Dataset) -> dict:
    """原文件行数 = 最终可用记录 + 清单内去重业务行数（同一业务行不重复计算）。"""
    items = db.query(CorrectionItem).filter(CorrectionItem.dataset_id == dataset.id).all()
    open_items = [item for item in items if item.status == CorrectionStatus.OPEN.value]
    fixed_items = [item for item in items if item.status == CorrectionStatus.FIXED.value]
    open_bad_rows = {(item.business_key, item.key_occurrence) for item in open_items}
    total_rows = int(dataset.row_count or 0)
    usable_rows = max(0, total_rows - len(open_bad_rows))
    last_run = (
        db.query(RuleRun)
        .filter(RuleRun.dataset_id == dataset.id, RuleRun.kind == "rules")
        .order_by(RuleRun.id.desc())
        .first()
    )
    return {
        "dataset_id": dataset.id,
        "business_key_column": dataset.business_key_column,
        "total_rows": total_rows,
        "open_entries": len(open_items),
        "open_bad_rows": len(open_bad_rows),
        "usable_rows": usable_rows,
        "fixed_entries": len(fixed_items),
        "balanced": usable_rows + len(open_bad_rows) == total_rows,
        "as_of_run_id": last_run.id if last_run else None,
    }


def run_effect(db: Session, run: RuleRun) -> dict:
    """单个批次对台账的结转：快照 + 本批次触碰过的清单条目。"""
    touched = (
        db.query(CorrectionItem)
        .filter(
            CorrectionItem.dataset_id == run.dataset_id,
            (
                (CorrectionItem.first_seen_run_id == run.id)
                | (CorrectionItem.last_seen_run_id == run.id)
                | (CorrectionItem.fixed_run_id == run.id)
            ),
        )
        .order_by(CorrectionItem.id.asc())
        .limit(200)
        .all()
    )
    return {"run_id": run.id, "effect": run.correction_json, "items": touched}


def reset_ledger(db: Session, dataset_id: int, reason: str) -> int:
    """业务键列变更后台账身份失效，清空重建（下一次执行重新形成清单）。"""
    removed = (
        db.query(CorrectionItem)
        .filter(CorrectionItem.dataset_id == dataset_id)
        .delete(synchronize_session=False)
    )
    log_event("CORRECTION_KEY_RESET", dataset_id=dataset_id, reason=reason, removed=removed)
    return removed


def status_label(status: str) -> str:
    return CORRECTION_STATUS_LABELS.get(status, status)
