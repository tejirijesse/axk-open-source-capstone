//! Divides a released payment between the parties to a trade, atomically.
//!
//! The invariant is that the parts sum to exactly the whole. Not approximately:
//! integer division leaves a remainder, and a remainder that is dropped, or
//! left sitting in the contract, is a balance that drifts by a stroop per
//! settlement until somebody reconciles a year of it by hand. The remainder is
//! assigned to a named party instead.
//!
//! A split is written once, by the coordinator, and read by anyone. Both halves
//! of that matter: write-once so the division cannot be rewritten after the
//! parties agree to it, and coordinator-only so nobody else can get their
//! division in first.

#![no_std]

use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, token, Address, BytesN, Env, Vec,
};

/// Basis points in the whole.
const BPS: i128 = 10_000;

/// Ledgers per day at the ~5 s close time.
const DAY_LEDGERS: u32 = 17_280;
/// Persistent entries are bumped once their TTL falls below this.
const TTL_THRESHOLD: u32 = DAY_LEDGERS * 120;
/// TTL applied on each bump.
const TTL_EXTEND: u32 = DAY_LEDGERS * 180;

#[contracterror]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum Error {
    /// The share list is empty.
    NoShares = 1,
    /// Shares do not total exactly 10,000 bps.
    SharesDoNotSumToWhole = 2,
    /// A share is zero or negative.
    ShareNotPositive = 3,
    /// The trade already has a split.
    AlreadyConfigured = 4,
    /// The trade has no split.
    NotConfigured = 5,
    /// Payout amount must be greater than zero.
    AmountNotPositive = 6,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Share {
    /// Recipient.
    pub party: Address,
    /// Basis points. All shares for a trade must total exactly 10,000.
    pub bps: i128,
}

#[contracttype]
#[derive(Clone)]
enum Key {
    /// Instance: the only address allowed to configure splits.
    Coordinator,
    /// Persistent: `Vec<Share>` by trade id.
    Shares(BytesN<32>),
}

#[contract]
pub struct Splitter;

#[contractimpl]
impl Splitter {
    /// Set in the deploy transaction, so the role cannot be claimed by a
    /// stranger between deployment and first use.
    pub fn __constructor(env: Env, coordinator: Address) {
        env.storage()
            .instance()
            .set(&Key::Coordinator, &coordinator);
    }

    /// The address allowed to configure splits.
    pub fn coordinator(env: Env) -> Address {
        env.storage().instance().get(&Key::Coordinator).unwrap()
    }

    /// Records how a trade divides. Set once per trade, so the split cannot be
    /// rewritten after the parties have agreed to it.
    ///
    /// Restricted to the coordinator. Write-once and unrestricted together are
    /// the dangerous pair: `trade_id` is public from the moment the escrow is
    /// funded, so an open `configure` lets anyone record a division of their own
    /// first — one that pays them everything — and `distribute` is authorised by
    /// the account paying out, not by the parties, so it would honour it.
    pub fn configure(env: Env, trade_id: BytesN<32>, shares: Vec<Share>) -> Result<(), Error> {
        Self::coordinator(env.clone()).require_auth();

        if shares.is_empty() {
            return Err(Error::NoShares);
        }
        let key = Key::Shares(trade_id);
        if env.storage().persistent().has(&key) {
            return Err(Error::AlreadyConfigured);
        }

        let mut total: i128 = 0;
        for share in shares.iter() {
            if share.bps <= 0 {
                return Err(Error::ShareNotPositive);
            }
            total += share.bps;
        }
        if total != BPS {
            return Err(Error::SharesDoNotSumToWhole);
        }

        env.storage().persistent().set(&key, &shares);
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTEND);
        Ok(())
    }

    /// Returns the split for a trade.
    pub fn shares(env: Env, trade_id: BytesN<32>) -> Result<Vec<Share>, Error> {
        env.storage()
            .persistent()
            .get(&Key::Shares(trade_id))
            .ok_or(Error::NotConfigured)
    }

    /// Pays every party their share of `amount` from `from`.
    ///
    /// Authorised by `from`. The rounding remainder goes to the last share, which
    /// by convention is the cooperative, so the parts always sum to `amount` and
    /// nothing stays in this contract.
    pub fn distribute(
        env: Env,
        trade_id: BytesN<32>,
        token_id: Address,
        from: Address,
        amount: i128,
    ) -> Result<(), Error> {
        if amount <= 0 {
            return Err(Error::AmountNotPositive);
        }
        let shares = Self::shares(env.clone(), trade_id)?;
        from.require_auth();

        let client = token::Client::new(&env, &token_id);
        let last = shares.len() - 1;
        let mut paid: i128 = 0;

        for (i, share) in shares.iter().enumerate() {
            let part = if i as u32 == last {
                amount - paid
            } else {
                amount * share.bps / BPS
            };
            paid += part;
            if part > 0 {
                client.transfer(&from, &share.party, &part);
            }
        }

        Ok(())
    }
}

mod test;
