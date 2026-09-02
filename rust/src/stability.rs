// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Z-Pinch Core — ideal-MHD stability estimate kernels

//! Growth-rate estimate `gamma ~ k v_A` (Haines 2011 §5) and the Kadomtsev
//! m=0 criterion on the Bennett profile (Kadomtsev 1966), identical in
//! operation order to `scpn_z_pinch_core.physics.stability`.

/// Kadomtsev criterion evaluated at one dimensionless radius.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct KadomtsevAssessment {
    /// `-d ln p / d ln r = 4 x^2 / (1 + x^2)`.
    pub profile_exponent: f64,
    /// `beta = 1 / x^2`.
    pub local_beta: f64,
    /// `4 gamma_ad / (2 + gamma_ad beta)`.
    pub threshold: f64,
    /// `profile_exponent < threshold`.
    pub sausage_stable: bool,
}

/// Growth rate `k v_A` and its e-folding time.
#[must_use]
pub fn growth_rate_estimate(alfven_speed_m_s: f64, axial_wavenumber_per_m: f64) -> (f64, f64) {
    let growth_rate_per_s = axial_wavenumber_per_m * alfven_speed_m_s;
    (growth_rate_per_s, 1.0 / growth_rate_per_s)
}

/// Kadomtsev m=0 criterion on the Bennett profile at `x = r / a`.
#[must_use]
pub fn kadomtsev_assessment(radius_ratio: f64, adiabatic_index: f64) -> KadomtsevAssessment {
    let squared = radius_ratio * radius_ratio;
    let profile_exponent = 4.0 * squared / (1.0 + squared);
    let local_beta = 1.0 / squared;
    let threshold = 4.0 * adiabatic_index / (2.0 + adiabatic_index * local_beta);
    KadomtsevAssessment {
        profile_exponent,
        local_beta,
        threshold,
        sausage_stable: profile_exponent < threshold,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bennett_profile_is_sausage_unstable_for_five_thirds() {
        for x in [1.0e-3, 0.5, 1.0, 2.0, 1.0e3] {
            assert!(!kadomtsev_assessment(x, 5.0 / 3.0).sausage_stable);
        }
        assert!(kadomtsev_assessment(1.0, 2.5).sausage_stable);
        let k = kadomtsev_assessment(1.0, 5.0 / 3.0);
        assert_eq!(k.profile_exponent, 2.0);
        assert_eq!(k.local_beta, 1.0);
    }

    #[test]
    fn growth_rate_is_k_alfven() {
        let (rate, fold) = growth_rate_estimate(273_441.167_674_757_13, 200.0);
        assert_eq!(rate, 200.0 * 273_441.167_674_757_13);
        assert_eq!(fold, 1.0 / rate);
    }
}
