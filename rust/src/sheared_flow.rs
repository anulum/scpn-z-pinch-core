// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Z-Pinch Core — sheared-flow criterion kernel

//! Shumlak-Hartman kink threshold `0.1 k v_A` (PRL 75 (1995) 3285),
//! identical in operation order to
//! `scpn_z_pinch_core.physics.sheared_flow.minimum_stabilising_shear`.

/// Published coefficient of the threshold.
pub const SHUMLAK_HARTMAN_COEFFICIENT: f64 = 0.1;

/// Minimum stabilising shear `0.1 k v_A`.
#[must_use]
pub fn minimum_stabilising_shear(alfven_speed_m_s: f64, axial_wavenumber_per_m: f64) -> f64 {
    SHUMLAK_HARTMAN_COEFFICIENT * axial_wavenumber_per_m * alfven_speed_m_s
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn threshold_form() {
        assert_eq!(minimum_stabilising_shear(1.0e5, 200.0), 0.1 * 200.0 * 1.0e5);
    }
}
