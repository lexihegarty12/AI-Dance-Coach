# Technique Reference Library Plan

## Goal

Compare a dancer's movement with a small, clearly labeled reference set rather
than treating one universal posture as correct. Outputs should say whether a
measurement is inside or outside the selected reference range and should show
the camera limitations.

## First supported positions

Start with three positions or short phrases:

1. **First position / standing alignment** — baseline posture and turnout proxy.
2. **Passé balance** — torso stability, supporting-leg alignment, turnout proxy,
   and arm placement.
3. **Arabesque** — intentional torso inclination, supporting-leg alignment,
   turnout proxy, and arm placement.

These are starting labels, not universal standards. The reference ranges should
be filled using instructor or experienced-dancer review.

## Measurements

### Torso

- torso lean magnitude and direction;
- shoulder-center over hip-center alignment;
- balance sway during a held position.

### Lower body and turnout

- hip-knee-ankle alignment in the camera view;
- left/right leg angle relationships;
- foot-orientation proxy only when the feet are visible and the camera angle is
  appropriate.

Turnout must be reported as a 2D camera-dependent proxy. It should never be
presented as a definitive measurement of hip rotation.

### Arms

- shoulder-elbow-wrist angles;
- hand height relative to shoulder and head;
- left/right symmetry when symmetry is part of the selected position.

## Reference data to collect

For each position, record 3–5 short clips or still frames with:

- full body visible;
- fixed camera and consistent distance;
- front or three-quarter view documented;
- position label and phase of movement;
- consent status and source/license;
- instructor or experienced-dancer notes on acceptable variation.

Avoid using random internet images as ground truth. Licensed or public-domain
images may be used for visual explanation, but labeled video references are
more useful for calibrating movement metrics.

## Build order

1. Improve the current torso metric to include direction and confidence filtering.
2. Add position labels and reference ranges for first position.
3. Add arm-angle measurements for first position.
4. Add lower-body alignment and cautious turnout proxy.
5. Validate the same measurements on passé and arabesque.
6. Have an experienced dancer review five result examples before expanding scope.
