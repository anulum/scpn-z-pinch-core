# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — device configuration model errors

"""Error surface of the device configuration model."""

from __future__ import annotations


class DeviceConfigurationError(ValueError):
    """Raised when a device configuration value violates a model invariant.

    Every rejection carries the offending field and the violated bound in
    its message; nothing is clamped or silently corrected.
    """
