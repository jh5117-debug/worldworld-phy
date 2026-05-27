# PhyInOne Deprecation Plan

Conclusion: PhyInOne is no longer needed for the active project.

- Do not build PhyInOne manifests.
- Do not use PhyInOne for warm-up, reward calibration, DPO, or benchmark.
- Keep old PhyInOne data untouched; do not delete it without a separate explicit confirmation.
- `cam_physgeo.data.scan_phyinone` now returns no samples and prints a deprecation warning.
- `configs/cam_physgeo/data_phyinone.yaml` is marked deprecated.
- Active manifest sources are only `physion_official` and `physion_movingcam`.

The historical PhyInOne code is retained only so earlier work remains auditable.
