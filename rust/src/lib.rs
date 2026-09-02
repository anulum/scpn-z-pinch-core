// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Z-Pinch Core — native level-0 physics kernels

//! Native level-0 device-physics kernels of SCPN Z-Pinch Core.
//!
//! Every function mirrors one closed-form evaluation of the pure-Python
//! floor in `scpn_z_pinch_core.physics` with the identical operation
//! order, so the IEEE-754 double results agree bit for bit. The kernels
//! use only `+`, `-`, `*`, `/` and `sqrt` (all correctly rounded) plus
//! the integer power `x * x`; no transcendental beyond `sqrt` appears, and
//! the Coulomb logarithm is an input. Nothing here solves an equation and
//! no value describes a real machine; the design record is ADR 0005 of the
//! repository.

pub mod bennett;
pub mod pease_braginskii;
pub mod sheared_flow;
pub mod stability;

/// Vacuum permeability `mu0 = 4e-7 pi` in henry per metre, evaluated exactly
/// as the Python floor evaluates it.
pub const MU0: f64 = 4.0e-7 * std::f64::consts::PI;
/// Elementary charge in coulombs (exact SI 2019 value).
pub const ELEMENTARY_CHARGE_C: f64 = 1.602_176_634e-19;

#[cfg(feature = "python")]
mod python {
    use pyo3::prelude::*;

    /// Bennett equilibrium tuple, see `crate::bennett::bennett_equilibrium`.
    #[pyfunction]
    fn bennett_equilibrium(
        column_radius_m: f64,
        peak_current_ma: f64,
        ion_line_density_per_m: f64,
        ion_mass_kg: f64,
    ) -> (f64, f64, f64, f64, f64, f64, f64) {
        let e = crate::bennett::bennett_equilibrium(
            column_radius_m,
            peak_current_ma,
            ion_line_density_per_m,
            ion_mass_kg,
        );
        (
            e.current_a,
            e.temperature_ev,
            e.axis_density_per_m3,
            e.axis_pressure_pa,
            e.edge_field_t,
            e.alfven_speed_m_s,
            e.alfven_transit_time_s,
        )
    }

    /// Bennett density profile value, see `crate::bennett::density_at`.
    #[pyfunction]
    fn density_at(axis_density_per_m3: f64, scale_radius_m: f64, radius_m: f64) -> f64 {
        crate::bennett::density_at(axis_density_per_m3, scale_radius_m, radius_m)
    }

    /// Azimuthal field of the Bennett profile, see `crate::bennett::field_at`.
    #[pyfunction]
    fn field_at(current_a: f64, scale_radius_m: f64, radius_m: f64) -> f64 {
        crate::bennett::field_at(current_a, scale_radius_m, radius_m)
    }

    /// Growth-rate estimate, see `crate::stability::growth_rate_estimate`.
    #[pyfunction]
    fn growth_rate_estimate(alfven_speed_m_s: f64, axial_wavenumber_per_m: f64) -> (f64, f64) {
        crate::stability::growth_rate_estimate(alfven_speed_m_s, axial_wavenumber_per_m)
    }

    /// Kadomtsev assessment, see `crate::stability::kadomtsev_assessment`.
    #[pyfunction]
    fn kadomtsev_assessment(radius_ratio: f64, adiabatic_index: f64) -> (f64, f64, f64, bool) {
        let k = crate::stability::kadomtsev_assessment(radius_ratio, adiabatic_index);
        (
            k.profile_exponent,
            k.local_beta,
            k.threshold,
            k.sausage_stable,
        )
    }

    /// Shumlak-Hartman threshold, see `crate::sheared_flow::minimum_stabilising_shear`.
    #[pyfunction]
    fn minimum_stabilising_shear(alfven_speed_m_s: f64, axial_wavenumber_per_m: f64) -> f64 {
        crate::sheared_flow::minimum_stabilising_shear(alfven_speed_m_s, axial_wavenumber_per_m)
    }

    /// Pease-Braginskii current, see `crate::pease_braginskii::pease_braginskii_current`.
    #[pyfunction]
    fn pease_braginskii_current(coulomb_logarithm: f64, mean_ion_charge: f64) -> f64 {
        crate::pease_braginskii::pease_braginskii_current(coulomb_logarithm, mean_ion_charge)
    }

    /// Python module `scpn_z_pinch_native`.
    #[pymodule]
    fn scpn_z_pinch_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(bennett_equilibrium, m)?)?;
        m.add_function(wrap_pyfunction!(density_at, m)?)?;
        m.add_function(wrap_pyfunction!(field_at, m)?)?;
        m.add_function(wrap_pyfunction!(growth_rate_estimate, m)?)?;
        m.add_function(wrap_pyfunction!(kadomtsev_assessment, m)?)?;
        m.add_function(wrap_pyfunction!(minimum_stabilising_shear, m)?)?;
        m.add_function(wrap_pyfunction!(pease_braginskii_current, m)?)?;
        Ok(())
    }
}
