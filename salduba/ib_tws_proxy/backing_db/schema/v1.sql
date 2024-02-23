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

-- See https://interactivebrokers.github.io/tws-api/classIBApi_1_1ComboLeg.html
CREATE TABLE COMBO_LEG(
  id varchar(255) primary key,
  contract_fk varchar(255) not null,
  conid bigint not null,
  ratio bigint,
  action varchar(10) not null,
  exchange varchar(255),
  open_close int,
  short_sale_slot bigint,
  designated_location varchar(255),
  exempt_code int default 0
);

-- See https://interactivebrokers.github.io/tws-api/classIBApi_1_1DeltaNeutralContract.html
CREATE TABLE DELTA_NEUTRAL_CONTRACT(
  id varchar(255) primary key,
  conid bigint not null,
  delta decimal,
  price decimal
);

-- See: https://interactivebrokers.github.io/tws-api/classIBApi_1_1Contract.html
CREATE TABLE CONTRACT (
  id varchar(255) primary key,
  at timestamp not null,
  expires_on timestamp,
  status varchar(50) not null,
  conid bigint not null,
  symbol varchar(255) not null,
  sec_type varchar(10) not null,
  last_trade_date_or_contract_month  varchar(255),
  strike decimal(19, 2) not null,
  right  varchar(255),
  multiplier varchar(255),
  exchange varchar(255) not null,
  currency varchar(255) not null,
  local_symbol varchar(255),
  primary_exchange varchar(255) not null,
  trading_class varchar(255),
  include_expired boolean default FALSE,
  sec_id_type varchar(255),
  sec_id varchar(255),
  description varchar(255),
  issuer_id varchar(255),
  combo_legs_description varchar(255),
  delta_neutral_contract_fk varchar(255)
);

-- See https://interactivebrokers.github.io/tws-api/classIBApi_1_1TagValue.html
create table contract_detail_tag(
  id varchar(255) primary key,
  contract_fk varchar(255) not null,
  tag varchar(255) not null,
  val varchar(255) not null
);

-- See https://interactivebrokers.github.io/tws-api/classIBApi_1_1ContractDetails.html
CREATE TABLE CONTRACT_DETAILS(
  id varchar(255) primary key,
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
  suggested_size_increment DECIMAL
);

CREATE TABLE MOVEMENT(
  id varchar(255) primary key,
  at timestamp not null,
  batch varchar(255) not null,
  ref varchar(255) not null,
  trade bigint not null,
  currency varchar(255) not null,
  money bigint not null,
  override_exchange varchar(255)
);
