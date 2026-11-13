// Structures and globals of the USA 1.0 layout, as far as they are named. Offsets in the
// `/* 0x.. */` comments are what symbols users generate their constants from.
#ifndef MM3D_Z3D_H
#define MM3D_Z3D_H

#include <stdint.h>

typedef struct SaveData {
    /* 0x0000 */ char unk_0000[0x4];
    /* 0x0004 */ uint8_t isNight;
    /* 0x0005 */ char unk_0005[0x7];
    /* 0x000C */ int32_t day;
    /* 0x0010 */ int32_t totalDay;
    /* 0x0014 */ char unk_0014[0x4];
    /* 0x0018 */ uint16_t time; // 0x4000 is 6:00, 0xC000 is 18:00
    /* 0x001A */ char unk_001A[0x122E];
    /* 0x1248 */ uint8_t weekEventReg[100]; // flag n is byte n / 8, bit n % 8
    /* 0x12AC */ char unk_12AC[0x7DC];
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

// A cutscene script (.jdb), stored in its scene's _info.zsi. Its commands follow the header.
typedef struct CutsceneScript {
    /* 0x00 */ char magic[4]; // "\0BDJ"
    /* 0x04 */ char unk_04[0x8];
    /* 0x0C */ char name[0x20];
    /* 0x2C */ char unk_2C[0x4];
    /* 0x30 */ uint8_t commandCount[4]; // s32, read a byte at a time: scripts may be unaligned
    /* 0x34 */ uint8_t endFrame[2]; // u16, read the same way
    /* 0x36 */ char unk_36[0x2];
} CutsceneScript; // size = 0x38

// Every command starts with this; its entries follow.
typedef struct CsCmdHeader {
    /* 0x0 */ uint8_t id[4]; // u32
    /* 0x4 */ uint8_t count[4]; // s32 entries; CS_CMD_CAMERA: bytes of data
} CsCmdHeader; // size = 0x8

typedef struct CsCmdText {
    /* 0x0 */ uint16_t textId; // CS_TEXT_NONE: no text
    /* 0x2 */ uint16_t startFrame;
    /* 0x4 */ uint16_t endFrame; // held here while the box is open
    /* 0x6 */ uint16_t type;
    /* 0x8 */ uint16_t altTextId1; // follows the first answer of a choice, or replaces textId (types 4 and 5)
    /* 0xA */ uint16_t altTextId2; // follows any other answer
} CsCmdText; // size = 0xC

typedef struct CsCmdActorCue {
    /* 0x00 */ uint16_t id;
    /* 0x02 */ uint16_t startFrame;
    /* 0x04 */ uint16_t endFrame;
    /* 0x06 */ char unk_06[0x2A];
} CsCmdActorCue; // size = 0x30

#define CS_CMD_TEXT 10
#define CS_CMD_CAMERA 90
// Actor cue lists: 100..149, 200 (the player), 201 and 450..599.
#define CS_CMD_ACTOR_CUE_FIRST 100
#define CS_CMD_ACTOR_CUE_COUNT 50
#define CS_CMD_PLAYER_CUE 200
#define CS_CMD_ACTOR_CUE_201 201
#define CS_CMD_ACTOR_CUE_EXTRA_FIRST 450
#define CS_CMD_ACTOR_CUE_EXTRA_COUNT 150
// Lists of 12-byte entries; every other list holds 8-byte entries.
#define CS_CMD_TRANSITION_GENERAL 155
#define CS_CMD_FADE_OUT_SEQ 156
#define CS_CMD_TIME 157
#define CS_CMD_RUMBLE 400
#define CS_CMD_601 601
#define CS_CMD_604 604
#define CS_CMD_END -1
#define CS_ENTRY_SIZE 8
#define CS_ENTRY_SIZE_WIDE 12

#define CS_TEXT_NONE 0xFFFF
#define CS_TEXT_TYPE_DEFAULT 0
#define CS_TEXT_TYPE_OCARINA_ACTION 2
#define CS_TEXT_TYPE_3 3 // a choice whose first answer shows altTextId1 and asks again
#define CS_TEXT_TYPE_BOSSES_REMAINS 4
#define CS_TEXT_TYPE_ALL_NORMAL_MASKS 5

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

// The touch screen's screens (docs/ui.md); the values index gUiScreens.
#define UI_SCREEN_MAIN 1
#define UI_SCREEN_ITEMS 4
#define UI_SCREEN_COUNT 8

typedef struct UiScreenContext {
    /* 0x00 */ void* vtable;
    /* 0x04 */ char unk_04[0x4];
    /* 0x08 */ void* activeScreen; // the gUiScreens entry that is up
    /* 0x0C */ char unk_0C[0x4];
} UiScreenContext; // size = 0x10 (at least)

extern CommonData gCommonData; // 0x007751D8
extern PlayState* gPlayState; // 0x00667890
extern UiScreenContext gUiScreenContext; // 0x0072F5BC
extern void* gUiScreens[UI_SCREEN_COUNT]; // 0x00656B00

#endif
