from enum import StrEnum, IntEnum


class Country(StrEnum):
  SW = 'SW'
  NA = 'NA'
  SM = 'SM'
  IM = 'IM'
  BB = 'BB'
  GR = 'GR'
  FP = 'FP'
  LN = 'LN'
  JP = 'JP'
  AV = 'AV'
  US = 'US'


class Currency(StrEnum):
  UNKNOWN = 'UNKNOWN'
  EUR = "EUR"
  USD = "USD"
  CHF = "CHF"
  GBP = "GBP"
  JPY = "JPY"


class Exchange(StrEnum):
  NONE = 'NONE'
  UNKNOWN = 'UNKNOWN'
  NASDAQ = "NASDAQ"
  NYSE = 'NYSE'
  SMART = "SMART"
  EBS = "EBS"
  AEB = "AEB"
  BM = "BM"
  BVME = "BVME"
  ENEXT_BE = "ENEXT.BE"
  IBIS = "IBIS"
  SBF = "SBF"
  LSE = "LSE"
  TSEJ = "TSEJ"
  VSE = "VSE"
  ISLAND = "ISLAND"


class SecType(StrEnum):
  STK = "STK"


class Action(StrEnum):
  BUY = "BUY"
  SELL = "SELL"


class OrderTif(StrEnum):
  DAY = 'DAY'
  GTC = 'GTC'
  IOC = 'IOC'
  GTD = 'GTD'
  OPG = 'OPG'
  FOK = 'FOK'
  DTC = 'DTC'


class OrderType(StrEnum):
  LMT = 'LMT'
  LIT = 'LIT'
  MKT = 'MKT'


class TimeInForce(StrEnum):
  DAY = "DAY"
  GTC = "GTC"
  GTD = "GTD"
  IOC = "IOC"
  FOK = "FOK"
  DTC = "DTC"


# https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html
class OcaType(IntEnum):
  CANCEL_ALL = 1
  BLOCK_REDUCE = 2
  NO_BLOCK_REDUCE = 3


# https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html
class TriggerMethod(IntEnum):
  DEFAULT = 0
  DOUBLE_BID_ASK = 1
  LAST = 2
  DOUBLE_LAST = 3
  BID_ASK = 4
  LAST_OR_BID_ASK = 7
  MID_POINT = 8


# https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html
class Rule80A(StrEnum):
  INDIVIDUAL = "I"
  AGENCY = "A"
  AGENT_OTHER_MEMBER = "W"
  INDIVIDUAL_PTIA = "J"
  AGENCY_PTIS = "U"
  AGENT_OTHER_MEMBER_PTIA = 'M'
  INDIVIDUAL_PT = 'K'
  AGENCY_PT = 'Y'
  AGENCY_OTHER_MEMBER_PT = 'N'


class Origin(IntEnum):
  CUSTOMER = 0
  FIRM = 1


class ShortSaleSlot(IntEnum):
  BROKER = 1
  OTHER = 2


class AuctionStrategy(IntEnum):
  MATCH = 1
  IMPROVEMENT = 2
  TRANSPARENT = 3


class VolatilityType(IntEnum):
  DAILY = 1
  ANNUAL = 2


class ReferencePriceType(IntEnum):
  NBBO_AVERAGE = 1
  NBB_OR_NBO = 2


class HedgeType(StrEnum):
  DELTA = "D"
  BETA = "B"
  FX = "F"
  PAIR = "P"


class ClearingIntent(StrEnum):
  IB = 'IB'
  AWAY = 'Away'
  PTA = 'PTA'


class AlgoStrategy(StrEnum):
  ARRIVAL_PX = 'ArrivalPx'
  DARK_ICE = 'DarkIce'
  PCT_VOL = 'PctVol'
  TWAP = 'Twap'
  VWAP = 'Vwap'


class IbOrderStatus(StrEnum):
  """
  See:
  - `docs/tws_order_state.drawio.png`
  - `docs/tws_orders.md`
  - [EWrapper.orderStatus](https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html#a27ec36f07dff982f50968c8a8887d676)
  """
  PENDING_SUBMIT = 'PendingSubmit'
  PENDING_CANCEL = 'PendingCancel'
  PRE_SUBMITTED = 'PreSubmitted'
  SUBMITTED = 'Submitted'
  FILLED = 'Filled'
  CANCELED = 'Canceled'
  INACTIVE = 'Inactive'
  NEW = 'New'
  UNKNOWN = 'Unknown'
