# Complete Video Prompt Description Guide

This guide is for the next TDW camera-moving warmup data pass. The goal is to make every prompt specific enough for LingBot-Fast to preserve foreground objects, background layout, physical events, and camera motion.

## 1. Overall Principles

Each video prompt must describe:

- foreground objects;
- background / environment;
- physical event;
- camera motion;
- negative constraints.

The prompt should be explicit, but not noisy. Object-aware descriptions are useful only when paired with constraints that prevent hallucination.

## 2. Foreground Object Fields

For each visible foreground object, include as many of these fields as metadata allows:

- object id if available;
- color;
- shape;
- size;
- material;
- position;
- initial motion state;
- role in event;
- relation to other objects.

Example:

> A small red cube is above a large green cube and starts falling under gravity.

## 3. Background Fields

Describe the visible scene context:

- floor / table / mat;
- wall / room;
- container if any;
- color;
- material;
- whether the background should remain stable;
- relation to camera motion.

Example:

> The scene is on a light wooden tabletop with a plain wall background. The background should stay geometrically stable under camera motion.

## 4. Physics Event Fields

Each prompt must state:

- event type;
- actor object;
- target object;
- direction;
- contact / collision / falling / rolling / containment relation;
- expected after-event behavior.

Example:

> A moving green ball collides with a black cone from the left. After contact, both objects should move consistently as rigid bodies.

## 5. Camera Motion Fields

Each prompt should include:

- camera follows the provided trajectory;
- camera starts moving from frame 0;
- maintain camera-conditioned background parallax;
- do not reinterpret camera motion as object motion.

Example:

> Follow the provided orbit camera trajectory from the first frame while keeping the room layout geometrically stable.

## 6. Negative Constraints

Include negative constraints whenever possible:

- no extra objects;
- no object disappearance;
- no object duplication;
- no recoloring;
- no melting or morphing;
- preserve rigid shapes;
- preserve object count;
- preserve foreground/background separation.

## 7. Four Template Examples

### Drop

A [color] [shape] falls under gravity near/on a [color] [shape]. Preserve all initially visible objects. The falling object should remain rigid and keep its color and shape. Follow the provided camera trajectory from the first frame. Do not add, remove, duplicate, recolor, melt, or morph objects.

### Collision

A moving [color] [shape] collides with a [color] [shape] from [direction]. After contact, the objects should move consistently with a rigid-body collision. Preserve object count, colors, and shapes. Follow the provided camera trajectory from the first frame. Do not create extra objects.

### Roll

A [color] [shape] rolls across the [surface] from [direction] to [direction]. The object should remain rigid and keep its shape and color. Keep the background stable and follow the camera trajectory.

### Containment

A set of visible objects interacts with a [container description]. Preserve the container and all foreground objects. Objects should remain inside/around the container consistently. Do not duplicate or remove objects. Follow the camera trajectory.

## 8. Bad Prompt Examples

Bad:

> A synthetic indoor physical scene with camera motion.

Why it is not enough:

- it does not state object count;
- it does not name the foreground objects;
- it does not describe the physical event;
- it does not constrain colors, shapes, or rigidity;
- it does not forbid extra objects or object disappearance.

Better:

> A small red cube falls under gravity toward a large green cube on a yellow wooden mat. The room has a plain wall and blue floor. Follow the provided orbit camera trajectory from frame 0. Preserve both objects, their colors, and rigid shapes. Do not add, remove, duplicate, recolor, melt, or morph objects.

## 9. Next-Week Usage

Next week, use this guide to update the 1000-sample combined_prompt_v2 manifest before the next warmup. After that, run rollout review again and only consider quality-bounded hard negatives for later preference learning.
