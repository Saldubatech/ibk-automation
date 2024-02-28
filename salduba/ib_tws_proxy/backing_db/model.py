from typing import Any
from enum import StrEnum


class RecordMeta:
  common_fields: list[str] = ['id', 'at']

  def __init__(self, table: str, own_fields: list[str], db_version: int):
    self.db_version = db_version
    self.table = table
    self.own_fields = own_fields
    self.all_fields = RecordMeta.common_fields + own_fields
    self.counter = "Select count(id) from " + table
    self.selector = "Select "+','.join(self.all_fields) + " from " + table
    self.inserter = 'Insert into ' + table + '(' + ', '.join(self.all_fields) + ') '
    self.value_inserter = self.inserter + 'values (' + ', '.join(['?'] * len(self.all_fields)) + ');'
    self.updater = 'Update ' + table + ' set ' + ', '.join([f"{k} = ?" for k in self.all_fields])


class Record:
  def __init__(self, id: str, at: int, companion: RecordMeta, *argsv: list[Any]) -> None:
    self.id: str = id
    self.at: int = at
    self.companion: RecordMeta = companion
    for field, value in zip(companion.own_fields, argsv):
      self.__dict__[field] = value
      
  def values(self) -> tuple[Any]:
    return tuple(self.__dict__[f] for f in self.companion.all_fields)

  def __repr__(self) -> str:
    return str(self.__dict__)


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
  def hydrate(*argsv) -> 'ContractRecord':  # type: ignore
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

  nominalClause = "status = 'CONFIRMED'"

  @staticmethod
  def hydrate(*argsv) -> 'ContractRecord':  # type: ignore
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
