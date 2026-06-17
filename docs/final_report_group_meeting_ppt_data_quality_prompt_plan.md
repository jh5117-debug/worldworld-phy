# Final Report: Group Meeting PPT Data Quality and Prompt Plan

## Outputs

- PPTX: `local_assets/reports/presentations/group_meeting_data_quality_prompt_plan/slides/tdw_data_quality_prompt_plan_group_meeting.pptx`
- PDF preview: `local_assets/reports/presentations/group_meeting_data_quality_prompt_plan/pdf/tdw_data_quality_prompt_plan_group_meeting.pdf`
- Package zip: `local_assets/reports/presentations/group_meeting_data_quality_prompt_plan/package/tdw_data_quality_prompt_plan_group_meeting_package.zip`
- Speaker notes: `local_assets/reports/presentations/group_meeting_data_quality_prompt_plan/speaker_notes/speaker_notes.md`
- Prompt guide: `local_assets/reports/presentations/group_meeting_data_quality_prompt_plan/prompt_guide/complete_video_prompt_description_guide.md`
- Video index: `local_assets/reports/presentations/group_meeting_data_quality_prompt_plan/assets/video_index.csv`

Lightweight copies for Git review:

- `docs/complete_video_prompt_description_guide.md`
- `docs/speaker_notes_group_meeting_data_quality_prompt_plan.md`

## Theme

The deck is centered on TDW camera-moving data quality and prompt quality, not DPO. The main message is that the data pipeline is runnable, but current rollout quality remains too weak to rush into preference learning. The next step should be a stronger per-video prompt description standard and better candidate data before DPO.

## Selected Real Videos

The package includes 12 real MP4 files from H20:

- 4 TDW GT examples: drop, collision, roll, containment.
- 4 prompt-aware comparison examples: template-aware and object-aware drop/collision.
- 4 current StageA 1000 prompt_v2 four-column comparison examples: drop failure, collision hallucination, roll disappearance, containment with weak physics.

Each selected video has:

- packaged MP4 under `assets/videos/`;
- thumbnail under `assets/thumbnails/`;
- contact sheet under `assets/contact_sheets/`;
- metadata row in `assets/video_index.csv`.

## Embedded Video Status

Embedded video: false.

The PPT uses thumbnails and packaged video links rather than embedding MP4 files directly. This was chosen because the available build environment did not provide a reliable PowerPoint video-embedding backend. The package zip includes all referenced videos, thumbnails, contact sheets, and the video index.

## Slide Outline

1. TDW Camera-Moving Data and Prompt Quality: Current Progress.
2. Current TDW Visible-Motion Dataset.
3. Generic Prompt Is Not Enough.
4. A Complete Prompt Recipe for Each Video.
5. Prompt Template by Physical Event.
6. Current Rollout Quality Is Still Not Enough.
7. Visual Metrics: Slight Change, Not a Clear Win.
8. Next Week: Better Data Before Preference Training.

## PDF Preview

PDF preview was generated from the slide images. It is intended for quick review of layout/content; video playback is available through the packaged MP4 files.

## Safety

No training was run.
No DPO was run.
No TDW generation was run.
No rollout was run.
No reward scoring or reward calibration was run.
No local_assets artifacts were staged for Git.
