from dataclasses import dataclass
from typing import Optional

from salduba.ib_tws_proxy.backing_db.record import Record
from salduba.ib_tws_proxy.domain.enumerations import Currency, Exchange, SecType


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


@dataclass
class DeltaNeutralContractRecord(Record):
  conid: int
  delta: float
  price: float


@dataclass
class ContractRecord(Record):
  expires_on: Optional[int]
  conId: int
  symbol: str
  secType: SecType
  lastTradeDateOrContractMonth: Optional[str]
  strike: float
  right: Optional[str]
  multiplier: Optional[str]
  exchange: Exchange
  primaryExchange: Exchange
  currency: Currency
  localSymbol: Optional[str]
  tradingClass: Optional[str]
  secIdType: Optional[str]
  secId: Optional[str]
  combo_legs_description: Optional[str]
  delta_neutral_contract_fk: Optional[str]
  includeExpired: bool = False


@dataclass
class ComboLegRecord(Record):
  table = 'COMBO_LEG'
  contract_fk: str
  conId: int
  ratio: Optional[int]
  action: str
  exchange: Optional[Exchange]
  open_close: Optional[int]
  short_sale_slot: Optional[int]
  designated_location: Optional[str]
  exempt_code: int = 0


@dataclass
class ContractDetailTagRecord(Record):
  table = "CONTRACT_DETAIL_TAG"
  contract_fk: str
  tag: str
  val: str


contractDetailsCompanion = [
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
  ]


@dataclass
class ContractDetailsRecord(Record):
  table = "CONTRACT_DETAILS"
  expires_on: int
