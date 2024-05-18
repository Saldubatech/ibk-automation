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
CREATE TABLE DELTA_NEUTRAL_CONTRACT(
  id varchar(255) primary key,
  at timestamp not null,
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
  delta_neutral_contract_fk varchar(255),
  foreign key(delta_neutral_contract_fk) references DELTA_NEUTRAL_CONTRACT(id)
);

-- See https://interactivebrokers.github.io/tws-api/classIBApi_1_1ComboLeg.html
CREATE TABLE COMBO_LEG(
  id varchar(255) primary key,
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
  id varchar(255) primary key,
  at timestamp not null,
  contract_fk varchar(255) not null,
  tag varchar(255) not null,
  val varchar(255) not null,
  foreign key(contract_fk) references CONTRACT(id)
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
  suggested_size_increment DECIMAL,
  foreign key(contract_fk) references CONTRACT(id)
);

CREATE TABLE ORDER_T(
  id varchar(255) primary key,
  at timestamp not null,
  orderid bigint not null,
  solicited boolean,
  clientid bigint not null,
  permid bigint,
  action varchar(255) not null,
  totalquantity DECIMAL,
  ordertype varchar(255) not null,
  lmtPrice decimal,
  auxprice decimal,
  tif varchar(255),
  ocagroup varchar(255),
  ocatype varchar(255),
  orderref varchar(255),
  transmit boolean not null,
  parentid bigint,
  blockorder boolean,
  sweeptofill boolean,
  displaysize bigint,
  triggermethod bigint,
  outsiderth boolean,
  hidden boolean,
  goodaftertime varchar(255),
  goodtilldate varchar(255),
  overridepercentageconstraints boolean,
  rule80a varchar(255),
  allornone boolean,
  minqty bigint,
  percentoffset decimal,
  trailstopprice decimal,
  trailingpercent decimal,
  fagroup varchar(255),
  famethod varchar(255),
  fapercentage varchar(255),
  openclose varchar(255),
  origin bigint,
  shortsaleslot bigint,
  designatedlocation varchar(255),
  exemptcode bigint,
  discretionaryamt decimal,
  optoutsmartrouting boolean,
  auctionstrategy bigint,
  startingprice decimal,
  stockrefprice decimal,
  delta decimal,
  stockrangelower decimal,
  stockrangeupper decimal,
  volatility decimal,
  volatilitytype bigint,
  continuousupdate bigint,
  referencepricetype bigint,
  deltaneutralordertype varchar(255),
  deltaneutralauxprice decimal,
  deltaneutralconid bigint,
  deltaneutralsettlingfirm varchar(255),
  deltaneutralclearingaccount varchar(255),
  deltaneutralopenclose varchar(255),
  deltaneutralshortsale varchar(255),
  deltaneutralshortsaleslot varchar(255),
  deltaneutraldesignatedlocation varchar(255),
  basispoints decimal,
  basispointstype bigint,
  scaleinitlevelsize bigint,
  scalesubslevelsize bigint,
  scalepriceincrement decimal,
  scalepriceadjustvalue decimal,
  scalepriceadjustinterval int,
  scaleprofitoffset decimal,
  scaleautoreset boolean,
  scaleinitposition bigint,
  scaleinitfillqty bigint,
  scalerandompercent boolean,
  hedgetype  varchar(255),
  hedgeparam varchar(255),
  account varchar(255),
  settlingfirm varchar(255),
  clearingaccount varchar(255),
  clearingintent varchar(255),
  algostrategy varchar(255),
  whatif boolean,
  algoid varchar(255),
  notheld boolean,
  activestarttime varchar(255),
  activestoptime varchar(255),
  scaletable varchar(255),
  modelcode varchar(255),
  extoperator varchar(255),
  cashqty decimal,
  mifid2decisionmaker varchar(255),
  mifid2decisionalgo varchar(255),
  mifid2executiontrader varchar(255),
  mifid2executionalgo varchar(255),
  dontuseautopriceforhedge varchar(255),
  autocanceldate varchar(255),
  filledquantity decimal,
  reffuturesconid bigint,
  autocancelparent boolean,
  shareholder varchar(255),
  imbalanceonly boolean,
  routemarketabletobbo boolean,
  parentpermid bigint,
  advancederroroverride varchar(255),
  manualordertime varchar(255),
  mintradeqty bigint,
  mincompetesize bigint,
  competeagainstbestoffset decimal,
  midoffsetatwhole decimal,
  midoffsetathalf decimal,
  randomizesize boolean,
  randomizeprice boolean,
  referencecontractid bigint,
  ispeggedchangeamountdecrease boolean,
  peggedchangeamount decimal,
  referencechangeamount decimal,
  adjustedordertype varchar(255),
  triggerprice decimal,
  lmtpriceoffset decimal,
  adjustedstopprice decimal,
  adjustedtrailingamount decimal,
  conditionsignorerth boolean,
  conditionscancelorder boolean,
  isomscontainer boolean,
  discretionaryuptolimitprice boolean,
  usepricemgmtalgo boolean,
  duration bigint,
  posttoats bigint
);

CREATE TABLE MOVEMENT(
  id varchar(255) primary key,
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
