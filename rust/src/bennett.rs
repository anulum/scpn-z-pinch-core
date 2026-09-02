// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Z-Pinch Core — Bennett equilibrium kernel

//! Bennett equilibrium of a z-pinch column (Bennett 1934; Haines 2011 §2),
//! operation-for-operation identical to
//! `scpn_z_pinch_core.physics.bennett.bennett_equilibrium`.

use crate::{ELEMENTARY_CHARGE_C, MU0};

/// Closed-form Bennett equilibrium quantities (SI units in the names).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct BennettEquilibrium {
    /// Pinch current `I` in amperes.
    pub current_a: f64,
    /// Equal-species Bennett temperature in electronvolts.
    pub temperature_ev: f64,
    /// On-axis density `n_0 = N / (pi a^2)`.
    pub axis_density_per_m3: f64,
    /// On-axis pressure `p_0 = 2 n_0 k T`.
    pub axis_pressure_pa: f64,
    /// Azimuthal field at the scale radius `mu0 I / (4 pi a)`.
    pub edge_field_t: f64,
    /// Alfven speed `B_theta(a) / sqrt(mu0 n_0 m_i)`.
    pub alfven_speed_m_s: f64,
    /// Alfven transit time `a / v_A`.
    pub alfven_transit_time_s: f64,
}

/// Evaluate the Bennett equilibrium.
///
/// Inputs are the validated configuration values (validation lives in the
/// Python floor; the kernel assumes finite, strictly positive inputs).
#[must_use]
pub fn bennett_equilibrium(
    column_radius_m: f64,
    peak_current_ma: f64,
    ion_line_density_per_m: f64,
    ion_mass_kg: f64,
) -> BennettEquilibrium {
    let current_a = peak_current_ma * 1.0e6;
    let temperature_ev = MU0 * (current_a * current_a)
        / (16.0 * std::f64::consts::PI * ion_line_density_per_m * ELEMENTARY_CHARGE_C);
    let axis_density_per_m3 =
        ion_line_density_per_m / (std::f64::consts::PI * (column_radius_m * column_radius_m));
    let axis_pressure_pa = 2.0 * axis_density_per_m3 * temperature_ev * ELEMENTARY_CHARGE_C;
    let edge_field_t = MU0 * current_a / (4.0 * std::f64::consts::PI * column_radius_m);
    let alfven_speed_m_s = edge_field_t / (MU0 * axis_density_per_m3 * ion_mass_kg).sqrt();
    let alfven_transit_time_s = column_radius_m / alfven_speed_m_s;
    BennettEquilibrium {
        current_a,
        temperature_ev,
        axis_density_per_m3,
        axis_pressure_pa,
        edge_field_t,
        alfven_speed_m_s,
        alfven_transit_time_s,
    }
}

/// Bennett density profile `n_0 / (1 + (r / a)^2)^2`.
#[must_use]
pub fn density_at(axis_density_per_m3: f64, scale_radius_m: f64, radius_m: f64) -> f64 {
    let ratio = radius_m / scale_radius_m;
    let inner = 1.0 + ratio * ratio;
    axis_density_per_m3 / (inner * inner)
}

/// Azimuthal field of the Bennett profile `mu0 I r / (2 pi (a^2 + r^2))`.
#[must_use]
pub fn field_at(current_a: f64, scale_radius_m: f64, radius_m: f64) -> f64 {
    MU0 * current_a * radius_m
        / (2.0 * std::f64::consts::PI * (scale_radius_m * scale_radius_m + radius_m * radius_m))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pressure_balance_closes() {
        let e = bennett_equilibrium(0.005, 0.1, 1.0e18, 3.343_583_772_4e-27);
        let magnetic = 2.0 * e.edge_field_t * e.edge_field_t / MU0;
        assert!((e.axis_pressure_pa - magnetic).abs() <= 1.0e-15 * magnetic);
        assert_eq!(e.current_a, 1.0e5);
    }

    #[test]
    fn profile_and_field_at_the_scale_radius() {
        let e = bennett_equilibrium(0.005, 0.1, 1.0e18, 3.343_583_772_4e-27);
        let quarter = density_at(e.axis_density_per_m3, 0.005, 0.005);
        assert!((quarter - e.axis_density_per_m3 / 4.0).abs() <= 1.0e-15 * quarter);
        let edge = field_at(e.current_a, 0.005, 0.005);
        assert!((edge - e.edge_field_t).abs() <= 1.0e-15 * edge);
        assert_eq!(field_at(e.current_a, 0.005, 0.0), 0.0);
    }
}
