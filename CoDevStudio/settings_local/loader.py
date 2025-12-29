from __future__ import annotations

from importlib.util import find_spec
from types import ModuleType
from typing import Any

from .schema import AppSettings, DatabaseConfig


class LocalSettingsError(RuntimeError):
    """local 設定檔存在但不符合規範時，給出明確錯誤。"""


def _module_overrides(local: ModuleType, base: AppSettings) -> dict[str, Any]:
    """
    只允許覆蓋 schema 已定義欄位（排除 DATABASES，因為 DATABASES 要走專門 merge）
    """
    overrides: dict[str, Any] = {}
    for k in vars(base).keys():
        if k == "DATABASES":
            continue
        if hasattr(local, k):
            overrides[k] = getattr(local, k)
    return overrides


def load_settings() -> AppSettings:
    base = AppSettings()

    # local 不存在：正常情境
    if not find_spec("._local_settings", __package__):
        return base

    # local 存在：才 import
    from . import _local_settings as local

    # --- DATABASES：支援局部覆蓋，但必須是 DatabaseConfig ---
    databases = dict(base.DATABASES)

    if hasattr(local, "DATABASES"):
        if not isinstance(local.DATABASES, dict):
            raise LocalSettingsError("local.DATABASES must be a dict[str, DatabaseConfig]")

        for name, cfg in local.DATABASES.items():
            if not isinstance(cfg, DatabaseConfig):
                raise LocalSettingsError(
                    f"local.DATABASES['{name}'] must be DatabaseConfig, got {type(cfg)}"
                )

            base_cfg = databases.get(name)
            databases[name] = base_cfg.merged_non_empty(cfg) if base_cfg else cfg

    # --- 其他欄位覆蓋（不含 DATABASES） ---
    overrides = _module_overrides(local, base)

    # ✅ 一次組 kwargs，避免 DATABASES 重複傳入
    kwargs = {**vars(base), **overrides}
    kwargs["DATABASES"] = databases

    return AppSettings(**kwargs)
