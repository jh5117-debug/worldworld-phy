# GPU6 DISPLAY=:25 NVIDIA Debug Report

Status: blocked before root-side configuration.

Attempted root non-interactive SSH with BatchMode and ubuntu sudo non-interactive check. Root SSH required credentials and ubuntu sudo required a password, so the agent could not safely create `/etc/X11/tdw-xorg-gpu6.conf` or start `Xorg :25` without recording credentials.

No root password was recorded. DISPLAY=:8 was not killed or changed. Because GPU6 :25 was not configured, the GPU1-7 display setup and TDW multi-display smoke are skipped in this run.
