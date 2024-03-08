from typing import Any
from enum import StrEnum

from salduba.ib_tws_proxy.backing_db.record import RecordMeta, Record


db_version = 1


deltaNeutralCompanion = RecordMeta(
  'DELTA_NEUTRAL_CONTRACT', [
    'conid',
    'delta',
    'price'
  ],
  db_version
)


class DeltaNeutralContractRecord(Record):

  @staticmethod
  def hydrate(*argsv: Any) -> 'DeltaNeutralContractRecord':  # type: ignore
    return DeltaNeutralContractRecord(argsv[0], argsv[1], *argsv[2:])  # type: ignore

  def __init__(self, id: str, at: int, *argsv: list[Any]) -> None:
    super().__init__(id, at, deltaNeutralCompanion, *argsv)


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
  UNCONFIRMED = 'UNCONFIRMED'
  NOMINAL = 'NOMINAL'
  EXTRA = 'EXTRA'
  RETIRED = 'RETIRED'


contractCompanion = RecordMeta(
  'CONTRACT',
  [
    'alias',
    'expires_on',
    'status',
    'conid',
    'symbol',
    'sec_type',
    'last_trade_date_or_contract_month',
    'strike',
    'right',
    'multiplier',
    'exchange',
    'currency', 
    'local_symbol',
    'primary_exchange',
    'trading_class',
    'include_expired',
    'sec_id_type',
    'sec_id',
    'description',
    'issuer_id',
    'combo_legs_description',
    'delta_neutral_contract_fk'],
  db_version
)


class ContractRecord(Record):

  expiresAfterClause = "(expires_on is null or expires_on > ?)"
  aliasClause = "(UPPER(alias) = ?)"
  descriptionClause = "(UPPER(description) = ?)"
  statusClause = "(status = ?)"

  @staticmethod
  def hydrate(*argsv: Any) -> 'ContractRecord':  # type: ignore
    return ContractRecord(argsv[0], argsv[1], *argsv[2:])  # type: ignore

  def __init__(self, id: str, at: int, *argsv: Any) -> None:
    super().__init__(id, at, contractCompanion, *argsv)


comboLegCompanion = RecordMeta(
  'COMBO_LEG',
  [
    'contract_fk',
    'conid',
    'ratio',
    'action',
    'exchange',
    'open_close',
    'short_sale_slot',
    'designated_location',
    'exempt_code'
  ],
  db_version
)


class ComboLegRecord(Record):
  @staticmethod
  def hydrate(*argsv) -> 'ComboLegRecord':  # type: ignore
    return ComboLegRecord(argsv[0], argsv[1], *argsv[2:])  # type: ignore

  def __init__(self, id: str, at: int, *argsv: list[Any]) -> None:
    super().__init__(id, at, comboLegCompanion, *argsv)


contractDetailTagCompanion = RecordMeta(
  'CONTRACT_DETAIL_TAG',
  [
    'contract_fk',
    'tag',
    'val'
  ],
  db_version
)


class ContractDetailTagRecord(Record):
  @staticmethod
  def hydrate(*argsv) -> 'ContractDetailTagRecord':  # type: ignore
    return ContractDetailTagRecord(argsv[0], argsv[1], *argsv[2:])  # type: ignore

  def __init__(self, id: str, at: int, *argsv: list[Any]) -> None:
    super().__init__(id, at, contractDetailTagCompanion, *argsv)


movementCompanion = RecordMeta(
  'MOVEMENT',
  [
    'batch',
    'ref',
    'trade',
    'currency',
    'money',
    'override_exchange'
  ],
  db_version
)


class MovementRecord(Record):
  @staticmethod
  def hydrate(*argsv) -> 'MovementRecord':  # type: ignore
    return MovementRecord(argsv[0], argsv[1], *argsv[2:])  # type: ignore

  def __init__(self, id: str, at: int, *argsv: list[Any]) -> None:
    super().__init__(id, at, movementCompanion, *argsv)


contractDetailsCompanion = RecordMeta(
  'CONTRACT_DETAILS',
  [
    'expires_on',
    'contract_fk',
    'marketplace',
    'min_tick',
    'order_types',
    'valid_exchanges',
    'under_conid',
    'long_name',
    'contract_month',
    'industry',
    'category',
    'subcategory',
    'time_zone_id',
    'liquid_hours',
    'ev_rule',
    'ev_multiplier',
    'agg_group',
    # -- sec_id_list List<contract_detail_tag>
    'under_symbol',
    'under_sev_type',
    'market_rule_ids',
    'real_expiration_date',
    'last_trade_time',
    'stock_type',
    'cusip',
    'ratings',
    'desc_append',
    'bond_type',
    'coupon_type',
    'callable',
    'putable',
    'coupon',
    'convertible',
    'maturity',
    'issue_date',
    'next_option_date',
    'next_option_partial',
    'notes',
    'min_size',
    'size_increment',
    'suggested_size_increment'
  ],
  db_version
)


class ContractDetailsRecord(Record):
  @staticmethod
  def hydrate(*argsv) -> 'ContractDetailsRecord':  # type: ignore
    return ContractDetailsRecord(argsv[0], argsv[1], *argsv[2:])  # type: ignore

  def __init__(self, id: str, at: int, *argsv: list[Any]) -> None:
    super().__init__(id, at, contractDetailsCompanion, *argsv)
