from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class CorrectionItem(Base):
    """待修正清单条目 —— 跨批次的纠错台账。

    同一 (dataset_id, rule_id, business_key, key_occurrence) 永远只有一条记录：
    修正版整份重传后再次执行只在这本台账上结转（修好关闭 / 没修好继续），
    不会像 Issue 那样按批次重复生成。key_occurrence 区分同一文件里业务键
    重复出现的多行（例如 unique 规则命中的重复账号），保证每个物理行都有
    自己的台账身份，对账时 原文件行数 = 可用记录 + 清单内去重业务行 才能成立。
    """

    __tablename__ = "correction_items"
    __table_args__ = (
        UniqueConstraint("dataset_id", "rule_id", "business_key", "key_occurrence", name="uq_correction_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False, index=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("quality_rules.id"), nullable=True, index=True)
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    column_name: Mapped[str] = mapped_column(String(190), nullable=False, default="")
    # severity: Severity 快照，规则后续被改/被删时清单仍可读
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    business_key: Mapped[str] = mapped_column(String(190), nullable=False, default="", index=True)
    key_occurrence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # row_index 跟随最新一份文件；first_row_index 保留首次命中时的原行号
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    first_row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_expr: Mapped[str | None] = mapped_column(Text, nullable=True)
    # status: CorrectionStatus (open|fixed)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)
    first_seen_run_id: Mapped[int | None] = mapped_column(ForeignKey("rule_runs.id"), nullable=True)
    last_seen_run_id: Mapped[int | None] = mapped_column(ForeignKey("rule_runs.id"), nullable=True)
    fixed_run_id: Mapped[int | None] = mapped_column(ForeignKey("rule_runs.id"), nullable=True)
    fixed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    dataset = relationship("Dataset", back_populates="correction_items")
    rule = relationship("QualityRule")
