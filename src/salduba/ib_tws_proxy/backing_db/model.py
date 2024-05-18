from enum import StrEnum
from typing import Any, Self

from salduba.ib_tws_proxy.backing_db.record import Record, RecordMeta


class Schema:
    """
    @startuml (id=SCHEMA)
    hide spot

    title
    Backing DB Schema V1
    end title

    entity Contract {
      * id: uuid
      * at: datetime
      * status: EnumStr
      * connId: int
      * symbol: str
      * sec_type: str
      last_trade_date_or_contract_month: str
      * strike: float
      right: str
      multiplier: str
      * exchange: str
      * primary_exchange: str
      * currency: str
      local_symbol: str
      trading_class: str
      include_expired: bool
      sec_id_type: str
      sec_id: str
      * description: str
      issuer_id: str
    }

    entity Movement {
      * id: uuid
      * contract: FK
      * at: datetime
      * batch: str
      * ticker: str
      * trade: float (?)
      * nombre: str
      * symbol: str
      * raw_type: str
      * raw_country: str
      * ibk_type: EnumStr
      * currency, EnumStr
      * exchange: str
      * exchange2: str
    }

    Movement::contract }o-|| Contract::id
    @enduml
    """


db_version = 1


deltaNeutralCompanion = RecordMeta("DELTA_NEUTRAL_CONTRACT", ["conid", "delta", "price"], db_version)


class DeltaNeutralContractRecord(Record):
    @classmethod
    def hydrate(cls, *argsv: Any) -> Self:
        return cls(argsv[0], argsv[1], *argsv[2:])

    def __init__(self, rid: str, at: int, *args: *Any) -> None:
        super().__init__(rid, at, deltaNeutralCompanion, *args)


class ContractRecordStatus(StrEnum):
    """
    ```plantuml
    @startuml (id=CONTRACT_RECORD_STATUS)
    title
    Contract Record Status
    end title

    state UNCONFIRMED
    state NOMINAL
    state EXTRA
    state RETIRED

    [*] -> UNCONFIRMED
    UNCONFIRMED --> NOMINAL
    UNCONFIRMED --> EXTRA
    NOMINAL -> EXTRA
    NOMINAL <- EXTRA
    UNCONFIRMED ---> RETIRED
    NOMINAL --> RETIRED
    EXTRA --> RETIRED
    RETIRED -> [*]
    @enduml
    ```
    """

    UNCONFIRMED = "UNCONFIRMED"
    NOMINAL = "NOMINAL"
    EXTRA = "EXTRA"
    RETIRED = "RETIRED"


contractCompanion = RecordMeta(
    "CONTRACT",
    [
        "expires_on",
        "status",
        "conid",
        "symbol",
        "sec_type",
        "last_trade_date_or_contract_month",
        "strike",
        "right",
        "multiplier",
        "exchange",
        "currency",
        "local_symbol",
        "primary_exchange",
        "trading_class",
        "include_expired",
        "sec_id_type",
        "sec_id",
        "description",
        "issuer_id",
        "combo_legs_description",
        "delta_neutral_contract_fk",
    ],
    db_version,
)


class ContractRecord(Record):
    expiresAfterClause = "(expires_on is null or expires_on > ?)"
    symbolClause = "(UPPER(symbol) = ?)"
    secTypeClause = "(sec_type = ?)"
    conidClause = "(conid = ?)"
    currencyClause = "(currency = ?)"

    exchangeClause = "(exchange = ?)"
    aliasClause = "(UPPER(alias) = ?)"
    descriptionClause = "(UPPER(description) = ?)"
    statusClause = "(status = ?)"

    @classmethod
    def hydrate(cls, *args: list[str]) -> Self:
        return cls(args[0], args[1], *args[2:])  # type: ignore

    def __init__(self, rid: str, at: int, *argsv: Any) -> None:
        super().__init__(rid, at, contractCompanion, *argsv)


comboLegCompanion = RecordMeta(
    "COMBO_LEG",
    [
        "contract_fk",
        "conid",
        "ratio",
        "action",
        "exchange",
        "open_close",
        "short_sale_slot",
        "designated_location",
        "exempt_code",
    ],
    db_version,
)


class ComboLegRecord(Record):
    @staticmethod
    def hydrate(*args: list[Any]) -> "ComboLegRecord":
        return ComboLegRecord(args[0], args[1], *args[2:])  # type: ignore

    def __init__(self, rid: str, at: int, *argsv: list[Any]) -> None:
        super().__init__(rid, at, comboLegCompanion, *argsv)


contractDetailTagCompanion = RecordMeta("CONTRACT_DETAIL_TAG", ["contract_fk", "tag", "val"], db_version)


class ContractDetailTagRecord(Record):
    @staticmethod
    def hydrate(*args: *Any) -> "ContractDetailTagRecord":
        return ContractDetailTagRecord(args[0], args[1], *args[2:])

    def __init__(self, rid: str, at: int, *args: *Any) -> None:
        super().__init__(rid, at, contractDetailTagCompanion, *args)


contractDetailsCompanion = RecordMeta(
    "CONTRACT_DETAILS",
    [
        "expires_on",
        "contract_fk",
        "marketplace",
        "min_tick",
        "order_types",
        "valid_exchanges",
        "under_conid",
        "long_name",
        "contract_month",
        "industry",
        "category",
        "subcategory",
        "time_zone_id",
        "liquid_hours",
        "ev_rule",
        "ev_multiplier",
        "agg_group",
        # -- sec_id_list List<contract_detail_tag>
        "under_symbol",
        "under_sev_type",
        "market_rule_ids",
        "real_expiration_date",
        "last_trade_time",
        "stock_type",
        "cusip",
        "ratings",
        "desc_append",
        "bond_type",
        "coupon_type",
        "callable",
        "putable",
        "coupon",
        "convertible",
        "maturity",
        "issue_date",
        "next_option_date",
        "next_option_partial",
        "notes",
        "min_size",
        "size_increment",
        "suggested_size_increment",
    ],
    db_version,
)


class ContractDetailsRecord(Record):
    @staticmethod
    def hydrate(*args: *Any) -> "ContractDetailsRecord":
        return ContractDetailsRecord(args[0], args[1], *args[2:])

    def __init__(self, rid: str, at: int, *argsv: list[Any]) -> None:
        super().__init__(rid, at, contractDetailsCompanion, *argsv)
