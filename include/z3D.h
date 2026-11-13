// Structures and globals of the USA 1.0 layout, as far as they are named. Offsets in the
// `/* 0x.. */` comments are what symbols users generate their constants from.
#ifndef MM3D_Z3D_H
#define MM3D_Z3D_H

#include <stdint.h>

typedef struct SaveData {
    /* 0x0000 */ char unk_0000[0x1A88];
} SaveData; // size = 0x1A88

typedef struct CommonData {
    /* 0x00000 */ char unk_00000[0x8]; // start and scene
    /* 0x00008 */ SaveData save;
    /* 0x01A90 */ char unk_01A90[0x11B8C];
    /* 0x1361C */ int32_t setup; // 1 on the title screen, 0 in play
} CommonData;

typedef struct CutsceneContext {
    /* 0x000 */ char unk_000[0x20];
    /* 0x020 */ uint16_t frames;
    /* 0x022 */ char unk_022[0x23E];
    /* 0x260 */ void* script;
    /* 0x264 */ uint8_t state; // 2 while a script runs
} CutsceneContext;

typedef struct CutsceneScript {
    /* 0x00 */ char unk_00[0x34];
    /* 0x34 */ uint8_t endFrame[2]; // u16, read a byte at a time: scripts may be unaligned
} CutsceneScript;

typedef struct PlayState {
    /* 0x0000 */ char unk_0000[0x34];
    /* 0x0034 */ uint32_t buttonsPressed; // pressed this frame; bit 3 is Start
    /* 0x0038 */ char unk_0038[0x110];
    /* 0x0148 */ int16_t sceneNum;
    /* 0x014A */ char unk_014A[0x22DE];
    /* 0x2428 */ CutsceneContext csCtx;
    /* 0x2690 */ char unk_2690[0x5990];
    /* 0x8020 */ char msgCtx[0x4509];
    /* 0xC529 */ int8_t transitionTrigger; // 20 requests a scene transition
    /* 0xC52A */ char unk_C52A[0x4];
    /* 0xC52E */ int16_t nextEntrance;
} PlayState;

extern CommonData gCommonData; // 0x007751D8
extern PlayState* gPlayState; // 0x00667890

#endif
