# H20 Migration Audit Bundle

Decision: `MIGRATION_AUDIT_BUNDLE_READY`

## Status Counts

- `PASS`: 11
- `WARN`: 3

## Files

- `h20_hostname`: `PASS` -> `reports/migration/h20_hostname.txt`
- `migration_date`: `PASS` -> `reports/migration/migration_date.txt`
- `git_status_short`: `PASS` -> `reports/migration/git_status_short.txt`
  - command: `git status --short`
- `git_branch`: `PASS` -> `reports/migration/git_branch.txt`
  - command: `git branch --show-current`
- `git_log_30`: `PASS` -> `reports/migration/git_log_30.txt`
  - command: `git log --oneline --decorate -30`
- `df_h20_pai`: `WARN` -> `reports/migration/df_h20_pai.txt`
  - command: `df -h /home/nvme03 /home/nvme04 /mnt/workspace/hj/nas_hj`
  - notes: exit_code=1
- `repo_du_summary`: `PASS` -> `reports/migration/repo_du_summary.txt`
  - command: `du -sh . docs reports manifests configs cam_physgeo src`
- `environment_no_builds`: `WARN` -> `reports/migration/environment_no_builds.yml`
  - command: `conda env export --no-builds`
  - notes: conda_not_found
- `pip_freeze`: `PASS` -> `reports/migration/pip_freeze.txt`
  - command: `/usr/bin/python3 -m pip freeze`
- `python_version`: `PASS` -> `reports/migration/python_version.txt`
- `python_path`: `PASS` -> `reports/migration/python_path.txt`
- `nvidia_smi`: `WARN` -> `reports/migration/nvidia_smi.txt`
  - command: `/usr/bin/nvidia-smi`
  - notes: timeout=20s
- `torch_cuda_info`: `PASS` -> `reports/migration/torch_cuda_info.txt`
  - command: `/usr/bin/python3 -c 'import sys
print('"'"'python'"'"', sys.version)
try:
    import torch
    print('"'"'torch'"'"', torch.__version__)
    print('"'"'cuda'"'"', torch.version.cuda)
    print('"'"'cuda_available'"'"', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('"'"'device_count'"'"', torch.cuda.device_count())
        for i in range(torch.cuda.device_count()):
            print(i, torch.cuda.get_device_name(i))
except Exception as e:
    print('"'"'torch_import_error'"'"', repr(e))'`
- `untracked_large_files`: `PASS` -> `reports/migration/untracked_large_files.tsv`
  - command: `git ls-files --others --exclude-standard -z`
  - notes: large_untracked_count=0 threshold_mb=50

## Safety

- CPU/IO-only audit; no file copy, no deletion, no rsync execute.
- `nvidia-smi` is query-only; no GPU jobs are launched.
- `untracked_large_files.tsv` records large untracked files for operator review but does not delete them.
