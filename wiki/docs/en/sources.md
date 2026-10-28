---
title: Sources
---

# Sources

The only test for a number to enter the catalog: **can it be traced back to a first-party source?**

- `A` — cross-checked against the vendor manual / official document
- `B` — public product page or third-party compilation, not cross-checked
- `C` — relayed, lead only

## Vendor sites and official docs

| Source | Type | Covers |
|---|---|---|
| DAMIAO | Vendor site | Joint motors, controller boards |
| Lingzu RobStride | Vendor site + PDF specs | Joint motors |
| Unitree | Vendor site | Motors, 4D LiDAR |
| DJI RoboMaster | Vendor site + user manuals | Boards, motors, ESCs |
| Orbbec | Vendor site | Depth cameras |
| Livox | Vendor site | LiDAR |
| Intel RealSense (regional distributor) | Distributor site | Depth cameras |
| NVIDIA Jetson | Vendor site | Compute modules |
| D-Robotics RDK docs | Official docs | Edge computers |

Data files live under `data/`; every part row carries `source_tier`, `origin` and `last_checked`.
