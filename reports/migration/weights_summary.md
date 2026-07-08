# Required Weights Manifest Summary

- Candidate rows: 300
- Search roots: `/home/nvme03`, `/home/nvme04`, maxdepth 7.
- SHA policy: files <=256 MiB were hashed immediately; larger files are marked `DEFERRED_GT256MB_TO_AVOID_IO_STORM` and require explicit checksum run before execute migration.
- Copy policy: review candidates before copy; do not migrate old failed checkpoints or full `local_assets` by default.

Primary manifest: `reports/migration/required_weights_manifest.tsv`.
SHA status: `reports/migration/required_weights_sha256.txt`.
