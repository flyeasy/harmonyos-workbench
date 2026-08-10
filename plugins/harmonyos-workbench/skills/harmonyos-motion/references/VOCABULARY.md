<!-- Modified from dososo/HarmonyOS-Design commit 205afcbf1d8170239477a98a8472089d4ab7b86c for HarmonyOS Workbench. -->

# Motion vocabulary

Use the smallest matching term. Terms describe an observation; they do not prove a platform API or root cause.

## Input feedback

| Symptom | Term | Distinguish from |
| --- | --- | --- |
| immediate visual response on touch down | press feedback | confirmed business result |
| action occurs only after valid release | commit on release | touch-down feedback |
| leave and re-enter can cancel/re-arm | cancel and re-enter | a failed gesture recognizer |
| keyboard/remote current target | focus state | selected state |
| pointer affordance | hover state | focus state |
| short-lived control after scroll/tap | transient reveal / visibility window | permanent navigation |

## Gesture continuity and curves

| Symptom | Term | Diagnostic split |
| --- | --- | --- |
| object follows finger | direct tracking | sampled animation |
| release keeps gesture speed | velocity handoff | speed reset/long frame |
| new target continues from visible position | animation continuity | restart from model value |
| new input takes over animation | interruptible motion | queued transition |
| harder movement past edge | boundary resistance | hard clamp |
| release returns to stable point | settle | snap selects discrete point |
| inertial release scroll | fling | direct tracking |
| child and scroll container disagree | gesture competition | recognizer mismatch in automation |
| bounce around target | underdamped spring | critical/overdamped settle |
| release feels like a brake | velocity discontinuity | dropped frame |

Possible ArkUI directions: `curves.responsiveSpringMotion()` for tracking, `curves.springMotion()` or `curves.interpolatingSpring()` for settle, and `parallelGesture` / `priorityGesture` for competition. Verify availability and semantics on the target SDK.

## Transition and spatial relation

| Observation | Term |
| --- | --- |
| peer modes change | same-level transition |
| parent/child navigation | hierarchical transition |
| same object moves across views | shared element transition |
| card/container shape continues | shared container transition |
| only motion direction remains shared | shared momentum |
| no visible break between views | continuous-shot effect |
| one fades while another appears | crossfade |
| default and custom transition both run | transition stacking |

`geometryTransition()` and Navigation transitions are possible directions, not proof of implementation.

## Transient and asynchronous state

| Observation | Term |
| --- | --- |
| repeated feedback restarts/extends | retrigger |
| earlier timeout hides newer feedback | stale timer / generation guard missing |
| trigger, layout and click race | visibility race |
| input accepted locally | acknowledged |
| remote/device work in progress | pending |
| authority confirms result | confirmed |
| pre-confirmation update can recover | optimistic UI / rollback |
| animation implies an unconfirmed success | false completion |
| old response replaces new intent | out-of-order response |
| one flag mixes link/service/session | state-axis conflation |

## Lifecycle, geometry and adaptation

| Observation | Term |
| --- | --- |
| leaving view still receives callbacks | lifecycle leak |
| wrong page receives content | view-state leakage |
| system inset applied twice | double safe-area application |
| local IME/tool changes resize remote content | local/remote geometry coupling |
| frequent layout mutation causes churn | layout thrash |
| harness observes a false failure | harness false negative |
| same task changes shape for device/input | interaction normalization / polymorphic control |
| continuous container change | adaptive layout |
| breakpoint reflow or column change | responsive layout |
| self-drawn content needs AT structure | virtual accessibility nodes |
