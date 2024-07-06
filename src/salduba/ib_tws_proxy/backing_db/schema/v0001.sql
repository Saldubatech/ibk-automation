/*
  @startuml (id=SCHEMA)
  hide spot

  title
  Backing DB Schema Structure
  end title

  entity ContractDetailTag {
    * id: uuid
    * contract: FK
  }

  entity ComboLeg {
    * id: uuid
    * contract: FK
  }

  entity DeltaNeutralContract {
    * id: uuid
  }

  entity Contract {
    * id: uuid
    delta_neutral_contract: FK
  }

  entity ContractDetail {
    * id: uuid
    * contract: FK
  }

  entity Movement {
    * id: uuid
    * contract: FK
  }

  Movement::contract }o-|| Contract::id
  Contract::id ||-o{ ComboLeg::contract
  Contract |o-- DeltaNeutralContract
  Contract ||--o| ContractDetail
  ContractDetail ||-lo{ ContractDetailTag
  @enduml
  */


-- See https://interactivebrokers.github.io/tws-api/classIBApi_1_1DeltaNeutralContract.html
CREATE TABLE DELTA_NEUTRAL_CONTRACT (
   rid varchar(255) primary key,
  at timestamp not null,
  conid bigint not null,
  delta decimal,
  price decimal
);

-- See: https://ibkrcampus.com/ibkr-api-page/twsapi-doc/#contracts
CREATE TABLE CONTRACT (
   rid varchar(255) primary key,
  at timestamp not null,
  expires_on timestamp,
  con_id bigint not null,
  symbol varchar(255) not null,
  sec_type varchar(10) not null,
  last_trade_date_or_contract_month  varchar(255),
  strike decimal(19, 2) not null,
  right  varchar(255),
  multiplier varchar(255),
  lookup_exchange varchar(255) not null,
  exchange varchar(255) not null,
  currency varchar(255) not null,
  local_symbol varchar(255),
  primary_exchange varchar(255) not null,
  trading_class varchar(255),
  include_expired boolean default FALSE,
  sec_id_type varchar(255),
  sec_id varchar(255),
  combo_legs_description varchar(255),
  delta_neutral_contract_fk varchar(255),
  foreign key(delta_neutral_contract_fk) references DELTA_NEUTRAL_CONTRACT(id)
);

-- See https://interactivebrokers.github.io/tws-api/classIBApi_1_1ComboLeg.html
CREATE TABLE COMBO_LEG(
   rid varchar(255) primary key,
  at timestamp not null,
  contract_fk varchar(255) not null,
  conid bigint not null,
  ratio bigint,
  action varchar(10) not null,
  exchange varchar(255),
  open_close int,
  short_sale_slot bigint,
  designated_location varchar(255),
  exempt_code int default 0,
  foreign key(contract_fk) references CONTRACT(id)
);

-- See https://interactivebrokers.github.io/tws-api/classIBApi_1_1TagValue.html
create table contract_detail_tag(
   rid varchar(255) primary key,
  at timestamp not null,
  contract_fk varchar(255) not null,
  tag varchar(255) not null,
  val varchar(255) not null,
  foreign key(contract_fk) references CONTRACT(id)
);

-- See https://interactivebrokers.github.io/tws-api/classIBApi_1_1ContractDetails.html
CREATE TABLE CONTRACT_DETAILS(
   rid varchar(255) primary key,
  at timestamp not null,
  expires_on timestamp,
  contract_fk varchar(255) not null,
  marketplace varchar(255),
  min_tick DECIMAL,
  order_types  varchar(2048),
  valid_exchanges  varchar(2048),
  under_conid BIGINT,
  long_name varchar(255),
  contract_month varchar(255),
  industry varchar(255),
  category varchar(255),
  subcategory varchar(255),
  time_zone_id varchar(255),
  liquid_hours varchar(255),
  ev_rule varchar(255),
  ev_multiplier decimal,
  agg_group bigint,
  -- sec_id_list List<contract_detail_tag>
  under_symbol varchar(255),
  under_sev_type varchar(255),
  market_rule_ids varchar(4092),
  real_expiration_date varchar(255),
  last_trade_time varchar(255),
  stock_type varchar(255),
  cusip varchar(255) not null,
  ratings varchar(4096),
  desc_append varchar(4092),
  bond_type varchar(255),
  coupon_type varchar(255),
  callable BOOLEAN,
  putable BOOLEAN default FALSE,
  coupon DECIMAL,
  convertible BOOLEAN default FALSE,
  maturity varchar(255) default 'FALSE',
  issue_date varchar(255),
  next_option_date varchar(255),
  next_option_partial varchar(255),
  notes varchar(4092),
  min_size DECIMAL,
  size_increment DECIMAL,
  suggested_size_increment DECIMAL,
  foreign key(contract_fk) references CONTRACT(id)
);

CREATE TABLE ORDER_T(
   rid varchar(255) primary key,
  at timestamp not null,
  order_id bigint not null,
  client_id bigint not null,
  action varchar(255) not null,
  order_type varchar(255) not null,
  transmit boolean not null,
  perm_id bigint,
  solicited boolean,
  total_quantity DECIMAL,
  lmt_price decimal,
  aux_price decimal,
  tif varchar(255),
  oca_group varchar(255),
  oca_type varchar(255),
  order_ref varchar(255),
  parent_id bigint,
  block_order boolean,
  sweep_to_fill boolean,
  display_size bigint,
  trigger_method bigint,
  outside_rth boolean,
  hidden boolean,
  good_after_time varchar(255),
  good_till_date varchar(255),
  override_percentage_constraints boolean,
  rule80_a varchar(255),
  all_or_none boolean,
  min_qty bigint,
  percent_offset decimal,
  trail_stop_price decimal,
  trailing_percent decimal,
  fa_group varchar(255),
  fa_method varchar(255),
  fa_percentage varchar(255),
  open_close varchar(255),
  origin bigint,
  short_sale_slot bigint,
  designated_location varchar(255),
  exempt_code bigint,
  discretionary_amt decimal,
  opt_out_smart_routing boolean,
  auction_strategy bigint,
  starting_price decimal,
  stock_ref_price decimal,
  delta decimal,
  stock_range_lower decimal,
  stock_range_upper decimal,
  volatility decimal,
  volatility_type bigint,
  continuous_update bigint,
  reference_price_type bigint,
  delta_neutral_order_type varchar(255),
  delta_neutral_aux_price decimal,
  delta_neutral_con_id bigint,
  delta_neutral_settling_firm varchar(255),
  delta_neutral_clearing_account varchar(255),
  delta_neutral_open_close varchar(255),
  delta_neutral_short_sale varchar(255),
  delta_neutral_short_sale_slot varchar(255),
  delta_neutral_designated_location varchar(255),
  basis_points decimal,
  basis_points_type bigint,
  scale_init_level_size bigint,
  scale_subs_level_size bigint,
  scale_price_increment decimal,
  scale_price_adjust_value decimal,
  scale_price_adjust_interval int,
  scale_profit_offset decimal,
  scale_auto_reset boolean,
  scale_init_position bigint,
  scale_init_fill_qty bigint,
  scale_random_percent boolean,
  hedge_type  varchar(255),
  hedge_param varchar(255),
  account varchar(255),
  settling_firm varchar(255),
  clearing_account varchar(255),
  clearing_intent varchar(255),
  algo_strategy varchar(255),
  what_if boolean,
  algo_id varchar(255),
  not_held boolean,
  active_start_time varchar(255),
  active_stop_time varchar(255),
  scale_table varchar(255),
  model_code varchar(255),
  ext_operator varchar(255),
  cash_qty decimal,
  mifid2_decision_maker varchar(255),
  mifid2_decision_algo varchar(255),
  mifid2_execution_trader varchar(255),
  mifid2_execution_algo varchar(255),
  dont_use_auto_price_for_hedge varchar(255),
  auto_cancel_date varchar(255),
  filled_quantity decimal,
  ref_futures_con_id bigint,
  auto_cancel_parent boolean,
  shareholder varchar(255),
  imbalance_only boolean,
  route_marketable_to_bbo boolean,
  parent_perm_id bigint,
  mid_offset_at_half decimal,
  randomize_size boolean,
  randomize_price boolean,
  reference_contract_id bigint,
  is_pegged_change_amount_decrease boolean,
  pegged_change_amount decimal,
  reference_change_amount decimal,
  adjusted_order_type varchar(255),
  trigger_price decimal,
  lmt_price_offset decimal,
  adjusted_stop_price decimal,
  adjusted_trailing_amount decimal,
  conditions_ignore_rth boolean,
  conditions_cancel_order boolean,
  is_oms_container boolean,
  discretionary_up_to_limit_price boolean,
  use_price_mgmt_algo boolean
);

CREATE TABLE MOVEMENT (
  rid varchar(255) primary key,
  at timestamp not null,
  status varchar(255) not null,
  batch varchar(255) not null,
  ticker varchar(255) not null,
  trade bigint not null,
  nombre varchar(255) not null,
  symbol varchar(255) not null,
  raw_type varchar(255) not null,
  ibk_type varchar(255) not null,
  country varchar(255) not null,
  currency varchar(255) not null,
  exchange varchar(255) not null,
  exchange2 varchar(255),
  contract_fk varchar(255) not null,
  order_fk varchar(255),
  foreign key(contract_fk) references CONTRACT(id),
  foreign key(order_fk) references ORDER_T(id)
);
