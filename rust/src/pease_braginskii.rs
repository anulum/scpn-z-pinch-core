// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Z-Pinch Core — Pease-Braginskii current kernel

//! Pease-Braginskii current in the published closed form of Klir (2005),
//! arXiv:physics/0703207, eq. (2.20), with the NRL Plasma Formulary
//! coefficients converted to SI (temperature in joules); identical in
//! operation order to `scpn_z_pinch_core.physics.pease_braginskii`.

use crate::{ELEMENTARY_CHARGE_C, MU0};

/// NRL parallel Spitzer resistivity coefficient, ohm metre with `T` in eV.
pub const SPITZER_RESISTIVITY_OHM_M_EV: f64 = 1.03e-4;
/// NRL bremsstrahlung coefficient, watt per cubic metre with `T` in eV.
pub const BREMSSTRAHLUNG_W_M3_EV: f64 = 1.69e-38;

/// `sigma_0` in siemens per metre per joule^(3/2).
#[must_use]
pub fn spitzer_conductivity_coefficient() -> f64 {
    1.0 / (SPITZER_RESISTIVITY_OHM_M_EV * (ELEMENTARY_CHARGE_C * ELEMENTARY_CHARGE_C.sqrt()))
}

/// `A` in watt cubic metre per joule^(1/2).
#[must_use]
pub fn bremsstrahlung_coefficient() -> f64 {
    BREMSSTRAHLUNG_W_M3_EV / ELEMENTARY_CHARGE_C.sqrt()
}

/// `I_PB = (pi / mu0) sqrt(48 ln Lambda / (sigma_0 A)) (1 + z) / z`.
#[must_use]
pub fn pease_braginskii_current(coulomb_logarithm: f64, mean_ion_charge: f64) -> f64 {
    let root = (48.0 * coulomb_logarithm
        / (spitzer_conductivity_coefficient() * bremsstrahlung_coefficient()))
    .sqrt();
    (std::f64::consts::PI / MU0) * root * (1.0 + mean_ion_charge) / mean_ion_charge
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hydrogenic_reference_value() {
        let current = pease_braginskii_current(10.0, 1.0);
        assert!((current - 1.4e6).abs() < 0.03 * 1.4e6);
        assert!((current - 1.370_175_749_673_332_6e6).abs() < 1.0);
    }
}
