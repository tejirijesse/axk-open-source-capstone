//! Holds a buyer's payment against one trade until delivery is verified.
//!
//! The destination is fixed when the escrow is created. Nothing afterwards can
//! change it, which is the only guarantee here worth having: a compromised
//! verifier or admin can stall a release or let the deadline pass, but cannot
//! send the money somewhere else.

#![no_std]

use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, token, Address, BytesN, Env,
};

/// Ledgers per day at the ~5 s close time.
const DAY_LEDGERS: u32 = 17_280;
/// Trade entries are bumped once their TTL falls below this.
const TRADE_TTL_THRESHOLD: u32 = DAY_LEDGERS * 120;
/// TTL applied on each bump. Must outlive the longest deadline or the funds
/// would sit behind an archived entry.
const TRADE_TTL_EXTEND: u32 = DAY_LEDGERS * 180;

/// Longest allowed deadline from now. A trade nobody reads only gets the TTL
/// applied at `create` (180 days), so the deadline must fall inside it.
const MAX_TERM_SECONDS: u64 = 150 * 86_400;

/// The one question escrow asks the lot registry: who gets paid for this lot, if it passed
/// inspection. Declared as an interface rather than importing the registry crate, so the two
/// contracts deploy and upgrade independently.
#[soroban_sdk::contractclient(name = "RegistryClient")]
pub trait Registry {
    /// The cooperative to pay for `lot_id`, or `None` unless the lot is approved.
    fn approved_cooperative(env: Env, lot_id: BytesN<32>) -> Option<Address>;
}

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum Error {
    /// Verifier or registry is not set.
    NotInitialised = 2,
    /// A trade with this id already exists.
    TradeExists = 3,
    /// No trade exists for this id.
    NoSuchTrade = 4,
    /// The trade is not in `Funded` status.
    NotFunded = 5,
    /// Refund requested before the deadline.
    DeadlineNotReached = 6,
    /// Deadline is not in the future.
    DeadlineInPast = 7,
    /// Amount must be greater than zero.
    AmountNotPositive = 8,
    /// Deadline is beyond `MAX_TERM_SECONDS`.
    DeadlineTooFar = 9,
    /// The lot has not passed inspection in the registry.
    LotNotApproved = 10,
    /// The lot already backs a live escrow.
    LotInEscrow = 11,
}

#[contracttype]
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Status {
    /// Money held. Can be released or, after the deadline, refunded.
    Funded = 0,
    /// Paid to the destination. Terminal.
    Released = 1,
    /// Returned to the buyer. Terminal.
    Refunded = 2,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Trade {
    pub lot_id: BytesN<32>,
    pub buyer: Address,
    /// The lot's cooperative, fixed at creation.
    pub destination: Address,
    pub token: Address,
    pub amount: i128,
    /// Ledger timestamp after which anyone may refund.
    pub deadline: u64,
    pub status: Status,
}

#[contracttype]
#[derive(Clone)]
enum Key {
    /// Instance: signs `create` and `release`.
    Verifier,
    /// Instance: lot registry contract.
    Registry,
    /// Persistent: `Trade` by trade id.
    Trade(BytesN<32>),
    /// The trade a lot currently backs. Cleared on refund, kept on release (the lot is sold).
    LotTrade(BytesN<32>),
}

#[contract]
pub struct Escrow;

#[contractimpl]
impl Escrow {
    /// Runs inside the deploy transaction, so there is no window in which a
    /// stranger can claim the verifier role, or point the escrow at a different
    /// lot registry, on a freshly deployed instance.
    pub fn __constructor(env: Env, verifier: Address, registry: Address) {
        env.storage().instance().set(&Key::Verifier, &verifier);
        env.storage().instance().set(&Key::Registry, &registry);
    }

    /// The lot registry this escrow consults.
    pub fn registry(env: Env) -> Result<Address, Error> {
        env.storage()
            .instance()
            .get(&Key::Registry)
            .ok_or(Error::NotInitialised)
    }

    /// The address that must co-sign `create` and sign `release`.
    pub fn verifier(env: Env) -> Result<Address, Error> {
        env.storage()
            .instance()
            .get(&Key::Verifier)
            .ok_or(Error::NotInitialised)
    }

    /// Funds an escrow.
    ///
    /// Both the buyer and the verifier sign: the buyer because the money leaves
    /// their account, the verifier because `trade_id` is caller-supplied and a
    /// trade id can only be occupied once. Without the second signature anyone
    /// could fund a one-stroop trade under the id of a real one and block it,
    /// then take their stroop back at the deadline.
    ///
    /// The lot must have passed inspection in the lot registry, and the money is
    /// paid to the cooperative that registered it. There is no destination
    /// parameter: the buyer pays for inspected goods, and the only party who can
    /// receive that payment is the one the goods belong to.
    ///
    /// A lot backs one live escrow at a time, so the same inspected lot cannot be
    /// sold to two buyers. A refund frees it again.
    pub fn create(
        env: Env,
        trade_id: BytesN<32>,
        lot_id: BytesN<32>,
        buyer: Address,
        token_id: Address,
        amount: i128,
        deadline: u64,
    ) -> Result<(), Error> {
        if amount <= 0 {
            return Err(Error::AmountNotPositive);
        }
        let now = env.ledger().timestamp();
        if deadline <= now {
            return Err(Error::DeadlineInPast);
        }
        if deadline - now > MAX_TERM_SECONDS {
            return Err(Error::DeadlineTooFar);
        }
        let key = Key::Trade(trade_id.clone());
        if env.storage().persistent().has(&key) {
            return Err(Error::TradeExists);
        }
        let lot_key = Key::LotTrade(lot_id.clone());
        if env.storage().persistent().has(&lot_key) {
            return Err(Error::LotInEscrow);
        }
        let destination = RegistryClient::new(&env, &Self::registry(env.clone())?)
            .approved_cooperative(&lot_id)
            .ok_or(Error::LotNotApproved)?;
        buyer.require_auth();
        Self::verifier(env.clone())?.require_auth();

        // Effects before the token transfer.
        env.storage().persistent().set(
            &key,
            &Trade {
                lot_id: lot_id.clone(),
                buyer: buyer.clone(),
                destination,
                token: token_id.clone(),
                amount,
                deadline,
                status: Status::Funded,
            },
        );
        env.storage()
            .persistent()
            .extend_ttl(&key, TRADE_TTL_THRESHOLD, TRADE_TTL_EXTEND);
        env.storage().persistent().set(&lot_key, &trade_id);
        env.storage()
            .persistent()
            .extend_ttl(&lot_key, TRADE_TTL_THRESHOLD, TRADE_TTL_EXTEND);

        token::Client::new(&env, &token_id).transfer(
            &buyer,
            &env.current_contract_address(),
            &amount,
        );
        Ok(())
    }

    /// Pays the destination recorded at creation. The caller does not get to
    /// name it, so a compromised verifier cannot redirect the money.
    pub fn release(env: Env, trade_id: BytesN<32>) -> Result<(), Error> {
        Self::verifier(env.clone())?.require_auth();

        let key = Key::Trade(trade_id);
        let mut trade: Trade = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(Error::NoSuchTrade)?;
        if trade.status != Status::Funded {
            return Err(Error::NotFunded);
        }

        trade.status = Status::Released;
        env.storage().persistent().set(&key, &trade);
        env.storage()
            .persistent()
            .extend_ttl(&key, TRADE_TTL_THRESHOLD, TRADE_TTL_EXTEND);

        token::Client::new(&env, &trade.token).transfer(
            &env.current_contract_address(),
            &trade.destination,
            &trade.amount,
        );
        Ok(())
    }

    /// Returns the money to the buyer once the deadline has passed. Frees the lot.
    ///
    /// Callable by anyone. If it required a privileged caller, a
    /// buyer's refund would depend on AXK still being around to sign for it.
    pub fn refund(env: Env, trade_id: BytesN<32>) -> Result<(), Error> {
        let key = Key::Trade(trade_id);
        let mut trade: Trade = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(Error::NoSuchTrade)?;
        if trade.status != Status::Funded {
            return Err(Error::NotFunded);
        }
        if env.ledger().timestamp() < trade.deadline {
            return Err(Error::DeadlineNotReached);
        }

        trade.status = Status::Refunded;
        env.storage().persistent().set(&key, &trade);
        env.storage()
            .persistent()
            .remove(&Key::LotTrade(trade.lot_id.clone()));
        env.storage()
            .persistent()
            .extend_ttl(&key, TRADE_TTL_THRESHOLD, TRADE_TTL_EXTEND);

        token::Client::new(&env, &trade.token).transfer(
            &env.current_contract_address(),
            &trade.buyer,
            &trade.amount,
        );
        Ok(())
    }

    /// The trade this lot is backing, if any. None once a refund frees the lot.
    pub fn lot_trade(env: Env, lot_id: BytesN<32>) -> Option<BytesN<32>> {
        env.storage().persistent().get(&Key::LotTrade(lot_id))
    }

    /// Returns the trade and refreshes its TTL.
    pub fn get(env: Env, trade_id: BytesN<32>) -> Result<Trade, Error> {
        let key = Key::Trade(trade_id);
        let trade: Trade = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(Error::NoSuchTrade)?;
        env.storage()
            .persistent()
            .extend_ttl(&key, TRADE_TTL_THRESHOLD, TRADE_TTL_EXTEND);
        Ok(trade)
    }
}

mod test;
