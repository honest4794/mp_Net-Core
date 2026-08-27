# storyMode_motor_reset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `storyMode_motor_reset` servo mode that gradually closes all servos before switching back to LED storymode set.

**Architecture:** New independent state machine (INIT → CLOSE_TOP → CLOSE_MID → CLOSE_SKIRT → CLOSE_LEGS → END) in its own file, registered as the last entry in `servoStoryModes`. UART controller triggers it when Timer sends bit6=0 while in SERVO set; auto-switch-back logic in i2cController handles the LED transition after completion.

**Tech Stack:** C++ / PlatformIO / ESP32-S3 / FastLED

---

### Task 1: Add state enum and timing globals

**Files:**
- Modify: `firmware/shared/include/globals.h:98` (add time constant) and `:474` (add state enum after `STATE_MODE_SIGNALS`)
- Modify: `firmware/shared/include/globals.h:283` (add extern for startTime and state)
- Modify: `firmware/shared/src/globals.cpp:56` (add definitions)

- [ ] **Step 1: Add time constant default in `globals.h` after line 98**

After the existing `STORYMODE_MOTOR_TOTAL_SECONDS` block (line 96-98), add:

```cpp
#ifndef STORYMODE_MOTOR_RESET_TOTAL_SECONDS
#define STORYMODE_MOTOR_RESET_TOTAL_SECONDS 30  // 不要修改這裡！ 請到platformio_local.ini去定義
#endif
```

- [ ] **Step 2: Add state enum in `globals.h` after the `STATE_MODE_SIGNALS` enum (after line 474)**

```cpp
enum STATE_MODE_MOTOR_RESET {
    MODE_MOTOR_RESET_INIT,
    MODE_MOTOR_RESET_CLOSE_TOP,
    MODE_MOTOR_RESET_CLOSE_MID,
    MODE_MOTOR_RESET_CLOSE_SKIRT,
    MODE_MOTOR_RESET_CLOSE_LEGS,
    MODE_MOTOR_RESET_END
};
```

- [ ] **Step 3: Add extern declarations in `globals.h` near line 283 (near `startTime_mode_signals` and `modeSignalsState`)**

Near `extern unsigned long startTime_mode_signals;`:
```cpp
extern unsigned long startTime_motor_reset;
```

Near `extern STATE_MODE_SIGNALS modeSignalsState;`:
```cpp
extern STATE_MODE_MOTOR_RESET modeMotorResetState;
```

- [ ] **Step 4: Add definitions in `globals.cpp` near `startTime_mode_signals` (line 56)**

Near `unsigned long startTime_mode_signals = 0;`:
```cpp
unsigned long startTime_motor_reset = 0;
```

Near `STATE_MODE_SIGNALS modeSignalsState = MODE_SIGNALS_INIT;` (find it with grep):
```cpp
STATE_MODE_MOTOR_RESET modeMotorResetState = MODE_MOTOR_RESET_INIT;
```

- [ ] **Step 5: Verify compilation**

Run: `pio run -e slave1`
Expected: BUILD SUCCESS

- [ ] **Step 6: Commit**

```bash
git add firmware/shared/include/globals.h firmware/shared/src/globals.cpp
git commit -m "feat: add storyMode_motor_reset state enum and timing globals"
```

---

### Task 2: Create storyMode_motor_reset header and implementation

**Files:**
- Create: `firmware/shared/include/storymode/storyMode_motor_reset.h`
- Create: `firmware/shared/src/storymode/storyMode_motor_reset.cpp`

- [ ] **Step 1: Create header file**

```cpp
#ifndef STORYMODE_MOTOR_RESET_H
#define STORYMODE_MOTOR_RESET_H

#include <Arduino.h>

// Gradually closes all servos back to origin position (reverse of motor open sequence).
// Used as the last servo storymode; runs before switching back to LED set.
bool storyMode_motor_reset(uint8_t slaveId);

#endif
```

- [ ] **Step 2: Create implementation file**

The file follows the same pattern as `storyMode_motor.cpp` but only contains the close sequence (CLOSE_TOP → CLOSE_MID → CLOSE_SKIRT → CLOSE_LEGS → END). It uses its own state variable `modeMotorResetState` and timing variable `startTime_motor_reset` so it doesn't interfere with `storyMode_motor`.

```cpp
#include "../../include/storymode/storyMode_motor_reset.h"

#include <Arduino.h>
#include <FastLED.h>

#include "../../include/globals.h"
#include "../../include/ledController.h"
#include "../../include/lib/lib_effects.h"
#include "../../include/lib/lib_led.h"
#include "../../include/lib/lib_channel.h"
#include "../../include/lib/lib_rgb.h"
#include "../../include/palettes.h"
#include "../../include/patterns/patterns_led.h"
#include "../../include/patterns/patterns_matrix.h"
#include "../../include/patterns/patterns_channel.h"
#include "../../include/patterns/patterns_rgb.h"
#include "../../include/pwm/pwmConfig.h"
#include "../../include/storymode/storyModeController.h"
#include "../../include/storymode/storyMode_struct.h"
#include "../../include/storymode/storyMode_timing.h"
#include "../../include/utils.h"
#include "../../include/logger.h"
#include "../../include/storymode/storyMode_parameter.h"

using namespace sm_signals;

#define MOTOR_RESET_FWD_LIMIT MOTOR_DUTY_MAX
#define ADVANCE_MOTOR_RESET_STATE(nextState) \
    do { \
        startTime_motor_reset = storyModeAnimationMillis(); \
        modeMotorResetState = (nextState); \
    } while (0)
#define ELAPSED_MOTOR_RESET_STAGE() (storyModeAnimationMillis() - startTime_motor_reset)

static void renderMotorResetAllPwmBreath() {
    chBreathAll(12, chBrightnessLowLightdim_2, chBrightnessOnLow);
}

#define RETURN_MOTOR_RESET_FRAME() \
    do { \
        renderMotorResetAllPwmBreath(); \
        return false; \
    } while (0)

bool storyMode_motor_reset(uint8_t slaveId) {
    switch (modeMotorResetState) {
    case MODE_MOTOR_RESET_INIT:
        // All RGB off
        rgbOff(leds_RGB1,  NUM_LEDS_RGB1);
        rgbOff(leds_RGB2,  NUM_LEDS_RGB2);
        rgbOff(leds_RGB3,  NUM_LEDS_RGB3);
        rgbOff(leds_RGB4,  NUM_LEDS_RGB4);
        rgbOff(leds_RGB7,  NUM_LEDS_RGB7);
        rgbOff(leds_RGB8,  NUM_LEDS_RGB8);
        rgbOff(leds_RGB9,  NUM_LEDS_RGB9);
        rgbOff(leds_RGB10, NUM_LEDS_RGB10);
        rgbOff(leds_RGB11, NUM_LEDS_RGB11);
        rgbOff(leds_RGB12, NUM_LEDS_RGB12);

        // Assume all servos may be deployed — hold at forward limit so close sequence
        // always starts from a consistent position.
        slave3_headCur = slave3_headFwdLimit;
        slave3_chestCur = MOTOR_DUTY_MAX;
        slave3_fSkirtCur = MOTOR_DUTY_MAX;
        slave3_rSkirtCur = MOTOR_DUTY_MAX;
        slaveSignalsMotorCur[0] = MOTOR_DUTY_MAX;
        slaveSignalsMotorCur[1] = MOTOR_DUTY_MIN;
        slaveSignalsMotorCur[2] = MOTOR_DUTY_MAX;
        slaveSignalsMotorCur[3] = MOTOR_DUTY_MIN;
        slaveSignalsMotorCur[4] = MOTOR_DUTY_MAX;
        slaveSignalsMotorCur[5] = MOTOR_DUTY_MIN;
        slaveSignalsMotorCur[6] = MOTOR_DUTY_MIN;
        slaveSignalsMotorCur[7] = MOTOR_DUTY_MIN;

        if (slaveId == 11) {
            resetSlave11SignalsDcMotor();
        }

        ADVANCE_MOTOR_RESET_STATE(MODE_MOTOR_RESET_CLOSE_TOP);
        RETURN_MOTOR_RESET_FRAME();

    // ============ CLOSE_TOP — head closes first ============
    case MODE_MOTOR_RESET_CLOSE_TOP: {
        unsigned long elapsed = ELAPSED_MOTOR_RESET_STAGE();
        if (slaveId == 12) {
            renderSlave12PlatformSignalPwmLights();
        } else if (slaveId == 13) {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            rgbOff(leds_RGB2, NUM_LEDS_RGB2);
            rgbOff(leds_RGB3, NUM_LEDS_RGB3);
            rgbOff(leds_RGB7, NUM_LEDS_RGB7);
        } else if (slaveId == 14) {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            rgbOff(leds_RGB2, NUM_LEDS_RGB2);
            rgbOff(leds_RGB3, NUM_LEDS_RGB3);
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
        }

        switch (slaveId) {
        case 3: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            if (elapsed >= stage_greenHoldMs) {
                chFadeOut(espMotor[0], servoFadeStep, slave3_headCur);
            } else {
                chServoHold(espMotor[0], slave3_headFwdLimit);
            }
            for (int i = 1; i <= 5; i++) chServoHold(espMotor[i], MOTOR_RESET_FWD_LIMIT);
            chOn(pcaLed[PWM1*16+0], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+1], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+2], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+7], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+8], chBrightnessOnLow);
        } break;
        case 4: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            slaveSignalsMotorCur[2] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[3] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[4] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[5] = MOTOR_DUTY_MAX;
            chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
            chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
            chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
            chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
        } break;
        case 5: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            slaveSignalsMotorCur[2] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[3] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[4] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[5] = MOTOR_DUTY_MAX;
            chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
            chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
            chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
            chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
        } break;
        case 7: case 8: {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            chOn(pcaLed[PWM0*16+0], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+1], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+4], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+5], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+7], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+8], chBrightnessOnLow);
            for (int i = 0; i <= 5; i++) chServoHold(espMotor[i], MOTOR_RESET_FWD_LIMIT);
        } break;
        case 2: case 6: case 9: case 10: {
            rgbOff(leds_RGB8, NUM_LEDS_RGB8);
            rgbOff(leds_RGB10, NUM_LEDS_RGB10);
            rgbOff(leds_RGB12, NUM_LEDS_RGB12);
            slaveSignalsMotorCur[0] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[1] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[2] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[3] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[4] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[5] = MOTOR_DUTY_MIN;
            chServoHold(espMotor[0], slaveSignalsMotorCur[0]);
            chServoHold(espMotor[1], slaveSignalsMotorCur[1]);
            chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
            chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
            chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
            chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
        } break;
        case 11: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            for (int i = 0; i <= 15; i++) {
                if (i == 8) chOff(pcaLed[PWM0*16+i]);
                else chOn(pcaLed[PWM0*16+i], chBrightnessOnLow);
            }
        } break;
        default: break;
        }

        if (elapsed >= stage_totalMs) {
            ADVANCE_MOTOR_RESET_STATE(MODE_MOTOR_RESET_CLOSE_MID);
        }
        RETURN_MOTOR_RESET_FRAME();
    }

    // ============ CLOSE_MID — chest closes ============
    case MODE_MOTOR_RESET_CLOSE_MID: {
        unsigned long elapsed = ELAPSED_MOTOR_RESET_STAGE();
        if (slaveId == 12) {
            renderSlave12PlatformSignalPwmLights();
        } else if (slaveId == 13) {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            rgbOff(leds_RGB2, NUM_LEDS_RGB2);
            rgbOff(leds_RGB3, NUM_LEDS_RGB3);
            rgbOff(leds_RGB7, NUM_LEDS_RGB7);
        } else if (slaveId == 14) {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            rgbOff(leds_RGB2, NUM_LEDS_RGB2);
            rgbOff(leds_RGB3, NUM_LEDS_RGB3);
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
        }

        switch (slaveId) {
        case 3: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            if (elapsed >= stage_greenHoldMs) {
                chFadeOut(espMotor[1], servoFadeStep, slave3_chestCur);
            } else {
                chServoHold(espMotor[1], MOTOR_RESET_FWD_LIMIT);
            }
            chServoStop(espMotor[0]);   // head already closed
            for (int i = 2; i <= 5; i++) chServoHold(espMotor[i], MOTOR_RESET_FWD_LIMIT);
            chOn(pcaLed[PWM1*16+0], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+1], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+2], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+7], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+8], chBrightnessOnLow);
        } break;
        case 4: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            if (elapsed >= stage_greenHoldMs) {
                chFadeOut(espMotor[2], servoFadeStep, slaveSignalsMotorCur[2]);
                chFadeOut(espMotor[3], servoFadeStep, slaveSignalsMotorCur[3]);
                chFadeOut(espMotor[4], servoFadeStep, slaveSignalsMotorCur[4]);
                chFadeOut(espMotor[5], servoFadeStep, slaveSignalsMotorCur[5]);
            } else {
                slaveSignalsMotorCur[2] = MOTOR_DUTY_MAX;
                slaveSignalsMotorCur[3] = MOTOR_DUTY_MAX;
                slaveSignalsMotorCur[4] = MOTOR_DUTY_MAX;
                slaveSignalsMotorCur[5] = MOTOR_DUTY_MAX;
                chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
                chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
                chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
                chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
            }
        } break;
        case 5: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            if (elapsed >= stage_greenHoldMs) {
                chFadeOut(espMotor[2], servoFadeStep, slaveSignalsMotorCur[2]);
                chFadeOut(espMotor[3], servoFadeStep, slaveSignalsMotorCur[3]);
                chFadeOut(espMotor[4], servoFadeStep, slaveSignalsMotorCur[4]);
                chFadeOut(espMotor[5], servoFadeStep, slaveSignalsMotorCur[5]);
            } else {
                slaveSignalsMotorCur[2] = MOTOR_DUTY_MAX;
                slaveSignalsMotorCur[3] = MOTOR_DUTY_MAX;
                slaveSignalsMotorCur[4] = MOTOR_DUTY_MAX;
                slaveSignalsMotorCur[5] = MOTOR_DUTY_MAX;
                chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
                chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
                chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
                chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
            }
        } break;
        case 7: case 8: {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            chOn(pcaLed[PWM0*16+0], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+1], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+4], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+5], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+7], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+8], chBrightnessOnLow);
            chServoHold(espMotor[0], MOTOR_RESET_FWD_LIMIT);
            chServoStop(espMotor[1]);
        } break;
        case 2: case 6: case 9: case 10: {
            rgbOff(leds_RGB8, NUM_LEDS_RGB8);
            rgbOff(leds_RGB10, NUM_LEDS_RGB10);
            rgbOff(leds_RGB12, NUM_LEDS_RGB12);
            slaveSignalsMotorCur[0] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[1] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[2] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[3] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[4] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[5] = MOTOR_DUTY_MAX;
            chServoHold(espMotor[0], slaveSignalsMotorCur[0]);
            chServoHold(espMotor[1], slaveSignalsMotorCur[1]);
            chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
            chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
            chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
            chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
        } break;
        case 11: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            for (int i = 0; i <= 15; i++) {
                if (i == 8) chOff(pcaLed[PWM0*16+i]);
                else chOn(pcaLed[PWM0*16+i], chBrightnessOnLow);
            }
        } break;
        default: break;
        }

        if (elapsed >= stage_totalMs) {
            ADVANCE_MOTOR_RESET_STATE(MODE_MOTOR_RESET_CLOSE_SKIRT);
        }
        RETURN_MOTOR_RESET_FRAME();
    }

    // ============ CLOSE_SKIRT — front skirt closes ============
    case MODE_MOTOR_RESET_CLOSE_SKIRT: {
        unsigned long elapsed = ELAPSED_MOTOR_RESET_STAGE();
        if (slaveId == 12) {
            renderSlave12PlatformSignalPwmLights();
        } else if (slaveId == 13) {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            rgbOff(leds_RGB2, NUM_LEDS_RGB2);
            rgbOff(leds_RGB3, NUM_LEDS_RGB3);
            rgbOff(leds_RGB7, NUM_LEDS_RGB7);
        } else if (slaveId == 14) {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            rgbOff(leds_RGB2, NUM_LEDS_RGB2);
            rgbOff(leds_RGB3, NUM_LEDS_RGB3);
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
        }

        switch (slaveId) {
        case 3: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            if (elapsed >= stage_greenHoldMs) {
                chFadeOut(espMotor[2], servoFadeStep, slave3_fSkirtCur);
                chFadeOut(espMotor[3], servoFadeStep, slave3_fSkirtCur);
            } else {
                chServoHold(espMotor[2], MOTOR_RESET_FWD_LIMIT);
                chServoHold(espMotor[3], MOTOR_RESET_FWD_LIMIT);
            }
            chServoStop(espMotor[0]);
            chServoStop(espMotor[1]);
            chServoHold(espMotor[4], MOTOR_RESET_FWD_LIMIT);
            chServoHold(espMotor[5], MOTOR_RESET_FWD_LIMIT);
            chOn(pcaLed[PWM1*16+0], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+1], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+2], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+7], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+8], chBrightnessOnLow);
        } break;
        case 7: case 8: {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            chOn(pcaLed[PWM0*16+0], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+1], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+4], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+5], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+7], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+8], chBrightnessOnLow);
            chServoHold(espMotor[0], MOTOR_RESET_FWD_LIMIT);
            chServoStop(espMotor[1]);
        } break;
        case 4: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            slaveSignalsMotorCur[2] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[3] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[4] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[5] = MOTOR_DUTY_MIN;
            chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
            chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
            chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
            chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
        } break;
        case 5: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            slaveSignalsMotorCur[2] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[3] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[4] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[5] = MOTOR_DUTY_MIN;
            chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
            chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
            chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
            chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
        } break;
        case 2: case 6: case 9: case 10: {
            rgbOff(leds_RGB8, NUM_LEDS_RGB8);
            rgbOff(leds_RGB10, NUM_LEDS_RGB10);
            rgbOff(leds_RGB12, NUM_LEDS_RGB12);
            slaveSignalsMotorCur[0] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[1] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[2] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[3] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[4] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[5] = MOTOR_DUTY_MAX;
            chServoHold(espMotor[0], slaveSignalsMotorCur[0]);
            chServoHold(espMotor[1], slaveSignalsMotorCur[1]);
            chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
            chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
            chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
            chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
        } break;
        case 11: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            for (int i = 0; i <= 15; i++) {
                if (i == 8) chOff(pcaLed[PWM0*16+i]);
                else chOn(pcaLed[PWM0*16+i], chBrightnessOnLow);
            }
        } break;
        default: break;
        }

        if (elapsed >= stage_totalMs) {
            ADVANCE_MOTOR_RESET_STATE(MODE_MOTOR_RESET_CLOSE_LEGS);
        }
        RETURN_MOTOR_RESET_FRAME();
    }

    // ============ CLOSE_LEGS — legs close last ============
    case MODE_MOTOR_RESET_CLOSE_LEGS: {
        unsigned long elapsed = ELAPSED_MOTOR_RESET_STAGE();
        if (slaveId == 12) {
            renderSlave12PlatformSignalPwmLights();
        } else if (slaveId == 13) {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            rgbOff(leds_RGB2, NUM_LEDS_RGB2);
            rgbOff(leds_RGB3, NUM_LEDS_RGB3);
            rgbOff(leds_RGB7, NUM_LEDS_RGB7);
        } else if (slaveId == 14) {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            rgbOff(leds_RGB2, NUM_LEDS_RGB2);
            rgbOff(leds_RGB3, NUM_LEDS_RGB3);
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
        }

        switch (slaveId) {
        case 7: case 8: {
            rgbOff(leds_RGB1, NUM_LEDS_RGB1);
            chOn(pcaLed[PWM0*16+0], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+1], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+4], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+5], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+7], chBrightnessOnLow);
            chOn(pcaLed[PWM0*16+8], chBrightnessOnLow);
            chServoStop(espMotor[1]);
            if (elapsed < stage_greenHoldMs) {
                chServoHold(espMotor[0], MOTOR_RESET_FWD_LIMIT);
            } else if (elapsed - stage_greenHoldMs < stage_rampDurMs) {
                uint16_t duty = map(elapsed - stage_greenHoldMs, 0, stage_rampDurMs,
                                    MOTOR_DUTY_MAX, MOTOR_DUTY_MIN);
                chServoHold(espMotor[0], duty);
            } else {
                chServoStop(espMotor[0]);
            }
        } break;
        case 3: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            if (elapsed >= stage_greenHoldMs) {
                chFadeOut(espMotor[4], servoFadeStep, slave3_rSkirtCur);
                chFadeOut(espMotor[5], servoFadeStep, slave3_rSkirtCur);
            } else {
                chServoHold(espMotor[4], MOTOR_RESET_FWD_LIMIT);
                chServoHold(espMotor[5], MOTOR_RESET_FWD_LIMIT);
            }
            for (int i = 0; i <= 3; i++) chServoStop(espMotor[i]);
            chOn(pcaLed[PWM1*16+0], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+1], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+2], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+7], chBrightnessOnLow);
            chOn(pcaLed[PWM1*16+8], chBrightnessOnLow);
        } break;
        case 4: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            slaveSignalsMotorCur[2] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[3] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[4] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[5] = MOTOR_DUTY_MIN;
            chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
            chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
            chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
            chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
        } break;
        case 5: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            slaveSignalsMotorCur[2] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[3] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[4] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[5] = MOTOR_DUTY_MIN;
            chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
            chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
            chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
            chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
        } break;
        case 2: case 6: case 9: case 10: {
            rgbOff(leds_RGB8, NUM_LEDS_RGB8);
            rgbOff(leds_RGB10, NUM_LEDS_RGB10);
            rgbOff(leds_RGB12, NUM_LEDS_RGB12);
            slaveSignalsMotorCur[0] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[1] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[2] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[3] = MOTOR_DUTY_MAX;
            slaveSignalsMotorCur[4] = MOTOR_DUTY_MIN;
            slaveSignalsMotorCur[5] = MOTOR_DUTY_MAX;
            chServoHold(espMotor[0], slaveSignalsMotorCur[0]);
            chServoHold(espMotor[1], slaveSignalsMotorCur[1]);
            chServoHold(espMotor[2], slaveSignalsMotorCur[2]);
            chServoHold(espMotor[3], slaveSignalsMotorCur[3]);
            chServoHold(espMotor[4], slaveSignalsMotorCur[4]);
            chServoHold(espMotor[5], slaveSignalsMotorCur[5]);
        } break;
        case 11: {
            rgbOff(leds_RGB4, NUM_LEDS_RGB4);
            for (int i = 0; i <= 15; i++) {
                if (i == 8) chOff(pcaLed[PWM0*16+i]);
                else chOn(pcaLed[PWM0*16+i], chBrightnessOnLow);
            }
        } break;
        default: break;
        }

        if (elapsed >= stage_totalMs) {
            ADVANCE_MOTOR_RESET_STATE(MODE_MOTOR_RESET_END);
        }
        RETURN_MOTOR_RESET_FRAME();
    }

    case MODE_MOTOR_RESET_END:
        if (slaveId == 11) {
            resetSlave11SignalsDcMotor();
        }
        rgbOff(leds_RGB1,  NUM_LEDS_RGB1);
        rgbOff(leds_RGB2,  NUM_LEDS_RGB2);
        rgbOff(leds_RGB3,  NUM_LEDS_RGB3);
        rgbOff(leds_RGB4,  NUM_LEDS_RGB4);
        rgbOff(leds_RGB7,  NUM_LEDS_RGB7);
        rgbOff(leds_RGB8,  NUM_LEDS_RGB8);
        rgbOff(leds_RGB9,  NUM_LEDS_RGB9);
        rgbOff(leds_RGB10, NUM_LEDS_RGB10);
        rgbOff(leds_RGB11, NUM_LEDS_RGB11);
        rgbOff(leds_RGB12, NUM_LEDS_RGB12);
        chOriginMotors();
        return true;

    default:
        return false;
    }
}
```

- [ ] **Step 3: Verify compilation**

Run: `pio run -e slave1`
Expected: May fail because not yet registered — that's OK, just verify no syntax errors in the new files by checking compiler output.

- [ ] **Step 4: Commit**

```bash
git add firmware/shared/include/storymode/storyMode_motor_reset.h firmware/shared/src/storymode/storyMode_motor_reset.cpp
git commit -m "feat: add storyMode_motor_reset implementation (close sequence only)"
```

---

### Task 3: Register in storyModeController and resetModeState

**Files:**
- Modify: `firmware/shared/src/storymode/storyModeController.cpp:23` (add include)
- Modify: `firmware/shared/src/storymode/storyModeController.cpp:205-207` (add to servoStoryModes array)
- Modify: `firmware/shared/src/storymode/storyModeController.cpp:155` (add reset in resetModeState)

- [ ] **Step 1: Add include at line 23 (after storyMode_motor.h include)**

```cpp
#include "../../include/storymode/storyMode_motor_reset.h"
```

- [ ] **Step 2: Add to servoStoryModes array (line 205-207)**

Change:
```cpp
StoryModeAndNameList servoStoryModes = {
    {storyMode_motor, "可動模式", STORYMODE_MOTOR_TOTAL_SECONDS},
};
```

To:
```cpp
StoryModeAndNameList servoStoryModes = {
    {storyMode_motor, "可動模式", STORYMODE_MOTOR_TOTAL_SECONDS},
    {storyMode_motor_reset, "復位模式", STORYMODE_MOTOR_RESET_TOTAL_SECONDS},
};
```

- [ ] **Step 3: Add state reset in resetModeState() (after line 153, near other state resets)**

Add after `modeIdleState = MODE_IDLE_INIT;`:
```cpp
    modeMotorResetState = MODE_MOTOR_RESET_INIT;
```

Add after `startTime_idle = 0;`:
```cpp
    startTime_motor_reset = 0;
```

- [ ] **Step 4: Verify compilation**

Run: `pio run -e slave1`
Expected: BUILD SUCCESS

- [ ] **Step 5: Commit**

```bash
git add firmware/shared/src/storymode/storyModeController.cpp
git commit -m "feat: register storyMode_motor_reset in servoStoryModes array"
```

---

### Task 4: Modify UART controller to trigger motor_reset on bit6=0

**Files:**
- Modify: `firmware/master/src/uartController.cpp:127-136` (change set-switch logic)

- [ ] **Step 1: Change the set-switch block in uartController.cpp**

Find the block at line 127-136:
```cpp
      if (desiredSet != activeStorySet) {
        activeStorySet = desiredSet;
        broadcastStorySet(activeStorySet);
        resetModeState();
        currentModeId = 0xFF;  // sentinel: force the modeId below to apply
        modeId = 0;            // switching set always restarts at mode 0 (mode 0
                               // is always valid, so the sentinel never leaks)
        LOG_UART("RX SET: 切換 story set → %s，重置 modeId 0",
                 activeStorySet == STORY_SET_SERVO ? "SERVO" : "LED");
      }
```

Replace with:
```cpp
      if (desiredSet != activeStorySet) {
        if (desiredSet == STORY_SET_LED && activeStorySet == STORY_SET_SERVO) {
          // 切回 LED 前，先跳到 servo 組最後一個 mode（motor_reset）收回所有 servo
          uint8_t resetModeIdx = servoStoryModeCount - 1;
          if (currentModeId != resetModeIdx) {
            resetModeState();
            currentModeId = resetModeIdx;
            loopCurrentMode = false;
            setUARTVideoModeFromStoryMode(currentModeId, true);
            broadcastModeSet(currentModeId);
            LOG_UART("RX SET: SERVO→LED 要求，先跑復位模式 modeId %d", currentModeId);
          }
          // 不切換 activeStorySet；motor_reset 跑完後 auto-switch-back 會自動切到 LED
          continue;
        }
        activeStorySet = desiredSet;
        broadcastStorySet(activeStorySet);
        resetModeState();
        currentModeId = 0xFF;  // sentinel: force the modeId below to apply
        modeId = 0;            // switching set always restarts at mode 0
        LOG_UART("RX SET: 切換 story set → %s，重置 modeId 0",
                 activeStorySet == STORY_SET_SERVO ? "SERVO" : "LED");
      }
```

- [ ] **Step 2: Verify compilation**

Run: `pio run -e master`
Expected: BUILD SUCCESS

- [ ] **Step 3: Commit**

```bash
git add firmware/master/src/uartController.cpp
git commit -m "feat: trigger motor_reset before switching SERVO→LED on UART bit6=0"
```

---

### Task 5: Build all affected environments

**Files:** (none — verification only)

- [ ] **Step 1: Build master**

Run: `pio run -e master`
Expected: BUILD SUCCESS

- [ ] **Step 2: Build slave1**

Run: `pio run -e slave1`
Expected: BUILD SUCCESS

- [ ] **Step 3: Build standalone**

Run: `pio run -e slave_standalone`
Expected: BUILD SUCCESS

- [ ] **Step 4: Commit (if any fixes were needed)**

---

### Task 6: Update documentation

**Files:**
- Modify: `docs/motor/servo_storymode.md`
- Modify: `docs/storymode/storymode目錄.md`

- [ ] **Step 1: Update `docs/motor/servo_storymode.md`**

In section 1 概念, update the note at line 25 to reflect the current state:

Replace:
```
> 目前狀態：`servoStoryModes` 只有 1 個項目 `servoStoryMode_0`，且為 **stub**（`servoStoryMode_0.cpp` 回傳 `false`，尚未實作動作）。
```

With:
```
> 目前狀態：`servoStoryModes` 有 2 個項目：`storyMode_motor`（可動模式）與 `storyMode_motor_reset`（復位模式）。
```

In section 2 相關檔案, add rows for the new files:

```
| `firmware/shared/src/storymode/storyMode_motor_reset.cpp` | 復位模式實作（close sequence only） |
| `firmware/shared/include/storymode/storyMode_motor_reset.h` | 復位模式宣告 |
```

Update the globals.h references to include:
```
| `firmware/shared/include/globals.h` | `STORYMODE_MOTOR_RESET_TOTAL_SECONDS` 預設（30 秒）、`STATE_MODE_MOTOR_RESET` enum |
```

In section 3 切換流程, add a note about the SERVO→LED reset behavior:

After the existing step 2, add:
```
   > **特殊情況：SERVO→LED 切換**
   > 當 Timer 發送 bit6=0（切到 LED 組）而 Master 目前在 SERVO 組時，Master 不會立即切換。
   > 而是先跳到 servo 組的最後一個 mode（`storyMode_motor_reset`），讓所有 servo 逐段收回。
   > 收回完成後，既有的 auto-switch-back 邏輯自動切回 LED 組。
```

- [ ] **Step 2: Update `docs/storymode/storymode目錄.md`**

In the Servo StoryMode Set table, replace the existing content with:

```
| 編號 | 函式 | 名稱 | 預設秒數 |
|------|------|------|----------|
| 0 | `storyMode_motor` | 可動模式 | 82s |
| 1 | `storyMode_motor_reset` | 復位模式 | 30s |
```

- [ ] **Step 3: Commit**

```bash
git add docs/motor/servo_storymode.md docs/storymode/storymode目錄.md
git commit -m "docs: add storyMode_motor_reset to servo storymode docs"
```
