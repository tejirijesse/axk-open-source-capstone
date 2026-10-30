//! Records that a commodity lot exists and that an authorised inspector examined it.
//!
//! This is the verification half of the trade. A cooperative registers a lot by committing
//! to a digest of its record (commodity, grade, weight, origin, the harvest records it
//! aggregates). An inspector then signs one inspection against it: pass or fail, the grade
//! and weight they measured, and a digest of their report. The escrow contract asks this
//! registry who the lot belongs to and whether it passed before it will take a buyer's money.
//!
//! Only digests go on-chain. The records themselves stay off-chain, so a buyer or lender
//! shown the record can hash it and check it against what was registered, without the ledger
//! carrying anybody's personal or commercial data.

#![no_std]

use soroban_sdk::{
    contract, contracterror, contractimpl, contracttype, symbol_short, xdr::ToXdr, Address, Bytes,
    BytesN, Env, Symbol,
};

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
    /// A lot with this id is already registered.
    LotExists = 1,
    /// No lot (or inspection) exists for this id.
    NoSuchLot = 2,
    /// The signer is not on the inspector list.
    NotAnInspector = 3,
    /// The lot already has its one inspection.
    AlreadyInspected = 4,
    /// Inspected quantity must be greater than zero.
    QuantityNotPositive = 5,
    /// The inspector is the cooperative that owns the lot.
    InspectorOwnsLot = 6,
}

#[contracttype]
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LotStatus {
    /// Awaiting inspection.
    Registered = 0,
    /// Passed inspection. Payable.
    Approved = 1,
    /// Failed inspection. Terminal.
    Rejected = 2,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Inspection {
    pub inspector: Address,
    pub passed: bool,
    /// Grade as measured by the inspector.
    pub grade: Symbol,
    /// Weight as measured, in kilograms. Always positive.
    pub quantity_kg: i128,
    /// Digest of the off-chain inspection report.
    pub report_digest: BytesN<32>,
    pub ledger: u32,
    pub timestamp: u64,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Lot {
    /// Owner, and the payee if the lot is approved.
    pub cooperative: Address,
    /// The cooperative's own reference. Not unique across cooperatives; see `lot_id`.
    pub lot_ref: BytesN<32>,
    /// Digest of the off-chain lot record.
    pub digest: BytesN<32>,
    pub status: LotStatus,
    pub registered_ledger: u32,
}

#[contracttype]
#[derive(Clone)]
enum Key {
    /// Instance: admin address.
    Admin,
    /// Persistent: presence means authorised.
    Inspector(Address),
    /// Persistent: `Lot` by lot id.
    Lot(BytesN<32>),
    /// Persistent: `Inspection` by lot id.
    Inspection(BytesN<32>),
}

#[contract]
pub struct LotRegistry;

#[contractimpl]
impl LotRegistry {
    /// Set in the deploy transaction, so the admin role cannot be claimed by a stranger
    /// between deployment and first use.
    pub fn __constructor(env: Env, admin: Address) {
        env.storage().instance().set(&Key::Admin, &admin);
    }

    /// The address that manages the inspector list.
    pub fn admin(env: Env) -> Address {
        env.storage().instance().get(&Key::Admin).unwrap()
    }

    /// Authorises an inspector. Admin only.
    pub fn add_inspector(env: Env, inspector: Address) {
        Self::admin(env.clone()).require_auth();
        env.storage()
            .persistent()
            .set(&Key::Inspector(inspector.clone()), &true);
        env.storage().persistent().extend_ttl(
            &Key::Inspector(inspector.clone()),
            TTL_THRESHOLD,
            TTL_EXTEND,
        );
        env.events()
            .publish((symbol_short!("insp"), symbol_short!("added")), inspector);
    }

    /// Withdraws an inspector's authority for future inspections. Inspections they already
    /// signed stand: they were valid when made, and rewriting history is what this contract
    /// exists to prevent.
    pub fn remove_inspector(env: Env, inspector: Address) {
        Self::admin(env.clone()).require_auth();
        env.storage()
            .persistent()
            .remove(&Key::Inspector(inspector.clone()));
        env.events()
            .publish((symbol_short!("insp"), symbol_short!("removed")), inspector);
    }

    /// Whether `inspector` is currently authorised.
    pub fn is_inspector(env: Env, inspector: Address) -> bool {
        env.storage().persistent().has(&Key::Inspector(inspector))
    }

    /// The on-chain id of a lot: sha256 over the cooperative's address and its own reference.
    ///
    /// Binding the id to the cooperative is what stops squatting. If the id were the bare
    /// reference, anyone could register a real lot's reference under their own address first,
    /// get it inspected by mistake, and be paid for somebody else's coffee. With the address
    /// folded in, a stranger registering the same reference produces a different lot.
    pub fn lot_id(env: Env, cooperative: Address, lot_ref: BytesN<32>) -> BytesN<32> {
        let mut preimage = Bytes::new(&env);
        preimage.append(&cooperative.to_xdr(&env));
        preimage.append(&Bytes::from(lot_ref));
        env.crypto().sha256(&preimage).into()
    }

    /// Registers a lot. Signed by the cooperative that owns it. Write-once.
    pub fn register_lot(
        env: Env,
        cooperative: Address,
        lot_ref: BytesN<32>,
        digest: BytesN<32>,
    ) -> Result<BytesN<32>, Error> {
        cooperative.require_auth();
        let id = Self::lot_id(env.clone(), cooperative.clone(), lot_ref.clone());
        let key = Key::Lot(id.clone());
        if env.storage().persistent().has(&key) {
            return Err(Error::LotExists);
        }
        env.storage().persistent().set(
            &key,
            &Lot {
                cooperative: cooperative.clone(),
                lot_ref,
                digest,
                status: LotStatus::Registered,
                registered_ledger: env.ledger().sequence(),
            },
        );
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTEND);
        env.events().publish(
            (symbol_short!("lot"), symbol_short!("register")),
            (id.clone(), cooperative),
        );
        Ok(id)
    }

    /// Records the one inspection of a lot. Signed by an authorised inspector who is not the
    /// cooperative that owns the lot.
    ///
    /// Write-once. A failed lot stays failed: re-inspecting until something passes is the
    /// behaviour an inspection record has to make visible, not permit. A cooperative that
    /// fixes a rejected lot registers it again under a new reference, and the rejection
    /// stays on the ledger.
    pub fn inspect(
        env: Env,
        lot_id: BytesN<32>,
        inspector: Address,
        passed: bool,
        grade: Symbol,
        quantity_kg: i128,
        report_digest: BytesN<32>,
    ) -> Result<LotStatus, Error> {
        inspector.require_auth();
        if !Self::is_inspector(env.clone(), inspector.clone()) {
            return Err(Error::NotAnInspector);
        }
        if quantity_kg <= 0 {
            return Err(Error::QuantityNotPositive);
        }
        let key = Key::Lot(lot_id.clone());
        let mut lot: Lot = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(Error::NoSuchLot)?;
        if lot.status != LotStatus::Registered {
            return Err(Error::AlreadyInspected);
        }
        if lot.cooperative == inspector {
            return Err(Error::InspectorOwnsLot);
        }

        lot.status = if passed {
            LotStatus::Approved
        } else {
            LotStatus::Rejected
        };
        let ikey = Key::Inspection(lot_id.clone());
        env.storage().persistent().set(
            &ikey,
            &Inspection {
                inspector: inspector.clone(),
                passed,
                grade,
                quantity_kg,
                report_digest,
                ledger: env.ledger().sequence(),
                timestamp: env.ledger().timestamp(),
            },
        );
        env.storage()
            .persistent()
            .extend_ttl(&ikey, TTL_THRESHOLD, TTL_EXTEND);
        env.storage().persistent().set(&key, &lot);
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTEND);
        env.events().publish(
            (symbol_short!("lot"), symbol_short!("inspect")),
            (lot_id, inspector, passed),
        );
        Ok(lot.status)
    }

    /// Returns the lot and refreshes its TTL.
    pub fn get(env: Env, lot_id: BytesN<32>) -> Result<Lot, Error> {
        let key = Key::Lot(lot_id);
        let lot: Lot = env
            .storage()
            .persistent()
            .get(&key)
            .ok_or(Error::NoSuchLot)?;
        env.storage()
            .persistent()
            .extend_ttl(&key, TTL_THRESHOLD, TTL_EXTEND);
        Ok(lot)
    }

    /// Returns the lot's inspection, or `NoSuchLot` if it has not been inspected.
    pub fn get_inspection(env: Env, lot_id: BytesN<32>) -> Result<Inspection, Error> {
        env.storage()
            .persistent()
            .get(&Key::Inspection(lot_id))
            .ok_or(Error::NoSuchLot)
    }

    /// The cooperative to pay for this lot, if and only if it passed inspection.
    /// This is the single question the escrow contract asks.
    pub fn approved_cooperative(env: Env, lot_id: BytesN<32>) -> Option<Address> {
        let lot: Lot = env.storage().persistent().get(&Key::Lot(lot_id))?;
        if lot.status == LotStatus::Approved {
            Some(lot.cooperative)
        } else {
            None
        }
    }

    /// True when `digest` is what the cooperative registered. The check a buyer or lender runs
    /// after hashing the lot record they were shown.
    pub fn matches(env: Env, lot_id: BytesN<32>, digest: BytesN<32>) -> bool {
        match env.storage().persistent().get::<_, Lot>(&Key::Lot(lot_id)) {
            Some(lot) => lot.digest == digest,
            None => false,
        }
    }
}

mod test;
