insert into delta_neutral_contract (
  id,
  conid,
  delta,
  price
) values (
  'dnc_id-001'
);

insert into contract (
  id,
  at,
  expires_on,
  status,
  conid,
  symbol,
  sec_type,
  last_trade_date_or_contract_month,
  strike,
  right,
  multiplier,
  exchange,
  currency,
  local_symbol,
  primary_exchange,
  trading_class,
  include_expired,
  sec_id_type,
  sec_id,
  description,
  issuer_id,
  combo_legs_description,
  delta_neutral_contract_fk
) values
(
  'asdf-asdf-asdf-0001', 
  123456,
  234567,
  'PENDING',
  012345,
  'SYMBOL',
  'STK',
  'MARCH',
  88.99,
  'RIGHT',
  'MULTIPLIER',
  'SMART',
  'USD',
  'LOC_SYMBOL',
  'NASDAQ',
  'TRD_CLASS',
  FALSE,
  'SEC_ID_TYPE',
  'SEC_ID',
  'Something or other',
  'Issuer',
  'The combo legs',
  'dnc_id-001');
