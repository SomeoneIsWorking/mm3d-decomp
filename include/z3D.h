// Structures and globals of the USA 1.0 layout, as far as they are named. Offsets in the
// `/* 0x.. */` comments are what symbols users generate their constants from.
#ifndef MM3D_Z3D_H
#define MM3D_Z3D_H

#include <stdint.h>

// Item buttons, in this order in both arrays (docs/items.md).
#define EQUIP_BUTTON_B 0
#define EQUIP_BUTTON_Y 1
#define EQUIP_BUTTON_X 2
#define EQUIP_BUTTON_I 3
#define EQUIP_BUTTON_II 4
#define ITEM_BOW 0x01
#define ITEM_NONE 0xFF
#define SLOT_BOW 1 // SaveData.items
#define INVENTORY_SLOTS 48 // items, then masks
// PlayState.buttonsHeld: the HID module's debug bit, which no 3DS button sets.
#define PAD_DEBUG 0x1000
#define PLAYER_FORM_HUMAN 4

typedef struct EquipmentData {
    /* 0x00 */ uint8_t buttonItems[4][5]; // item on each button; row 0 is Link's in human form
    /* 0x14 */ uint8_t buttonSlots[4][5]; // the inventory slot each item came from
    /* 0x28 */ uint16_t swordShield;
} EquipmentData; // size = 0x2A

typedef struct SaveData {
    /* 0x0000 */ char unk_0000[0x4];
    /* 0x0004 */ uint8_t isNight;
    /* 0x0005 */ char unk_0005[0x7];
    /* 0x000C */ int32_t day;
    /* 0x0010 */ int32_t totalDay;
    /* 0x0014 */ char unk_0014[0x4];
    /* 0x0018 */ uint16_t time; // 0x4000 is 6:00, 0xC000 is 18:00
    /* 0x001A */ char unk_001A[0x4];
    /* 0x001E */ uint8_t playerForm; // PLAYER_FORM_*
    /* 0x001F */ char unk_001F[0x113];
    /* 0x0132 */ uint16_t healthCapacity; // 0x10 a heart
    /* 0x0134 */ uint16_t health;
    /* 0x0136 */ char unk_0136[0x1];
    /* 0x0137 */ uint8_t magic; // 0x30 fills the single meter
    /* 0x0138 */ uint16_t rupees;
    /* 0x013A */ char unk_013A[0x4];
    /* 0x013E */ uint8_t magicAcquired; // the meter is drawn
    /* 0x013F */ uint8_t doubleMagicAcquired; // the meter is twice as long
    /* 0x0140 */ char unk_0140[0xA];
    /* 0x014A */ EquipmentData equipment;
    /* 0x0174 */ uint8_t items[24]; // by slot; the mask slots follow
    /* 0x018C */ uint8_t masks[24];
    /* 0x01A4 */ char unk_01A4[0xC];
    /* 0x01B0 */ uint8_t ammo[11]; // by item id (docs/hud.md)
    /* 0x01BB */ char unk_01BB[0x31];
    /* 0x01EC */ uint32_t upgrades; // UPGRADE_WALLET_*
    /* 0x01F0 */ uint32_t questItems; // bit 18: the Bombers' Notebook
    /* 0x01F4 */ char unk_01F4[0x1054];
    /* 0x1248 */ uint8_t weekEventReg[100]; // flag n is byte n / 8, bit n % 8
    /* 0x12AC */ char unk_12AC[0x7DC];
} SaveData; // size = 0x1A88

typedef struct CommonData {
    /* 0x00000 */ char unk_00000[0x8]; // start and scene
    /* 0x00008 */ SaveData save;
    /* 0x01A90 */ char unk_01A90[0x1A90];
    /* 0x03520 */ uint8_t motionOff; // the Motion Controls option: 0 is on (docs/motion.md)
    /* 0x03521 */ char unk_03521[0x100FB];
    /* 0x1361C */ int32_t setup; // 1 on the title screen, 0 in play
    /* 0x13620 */ char unk_13620[0x120];
    /* 0x13740 */ uint8_t buttonStatus[9]; // by EQUIP_BUTTON_*: BUTTON_ENABLED or BUTTON_DISABLED, set every frame
    /* 0x13749 */ char unk_13749[0x1];
    /* 0x1374A */ uint16_t nextHudVisibility; // set for a frame when the HUD is asked to change
    /* 0x1374C */ uint16_t hudVisibility; // HUD_VISIBILITY_*
    /* 0x1374E */ uint16_t hudVisibilityTimer;
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

typedef struct Vec3f {
    /* 0x0 */ float x;
    /* 0x4 */ float y;
    /* 0x8 */ float z;
} Vec3f; // size = 0xC

typedef struct PosRot {
    /* 0x00 */ Vec3f pos;
    /* 0x0C */ int16_t rot[3];
} PosRot; // size = 0x14

// The start of every actor (docs/actors.md); the names are the N64 game's.
typedef struct Actor {
    /* 0x000 */ int16_t id; // 0 is the player
    /* 0x002 */ uint8_t category; // ACTORCAT_*
    /* 0x003 */ int8_t room;
    /* 0x004 */ uint32_t flags;
    /* 0x008 */ PosRot home;
    /* 0x01C */ char unk_01C[0x8];
    /* 0x024 */ PosRot world;
    /* 0x038 */ char unk_038[0x4];
    /* 0x03C */ PosRot focus;
    /* 0x050 */ char unk_050[0x8];
    /* 0x058 */ Vec3f scale;
    /* 0x064 */ Vec3f velocity;
    /* 0x070 */ float speed;
    /* 0x074 */ float gravity;
    /* 0x078 */ float terminalVelocity;
    /* 0x07C */ char unk_07C[0x90];
    /* 0x10C */ Vec3f prevPos; // world.pos before this frame's update
    /* 0x118 */ char unk_118[0x2];
    /* 0x11A */ uint16_t textId; // the message a check or a talk opens
    /* 0x11C */ char unk_11C[0x18];
    /* 0x134 */ struct Actor* next; // in its category's list
} Actor; // size = 0x138 (at least)

// One actor category's list (docs/actors.md).
typedef struct ActorListEntry {
    /* 0x0 */ int32_t length;
    /* 0x4 */ struct Actor* head;
    /* 0x8 */ char unk_8[0x4];
} ActorListEntry; // size = 0xC

#define ACTORCAT_PLAYER 2
#define ACTORCAT_COUNT 12

typedef struct ActorContext {
    /* 0x00 */ char unk_00[0x10];
    /* 0x10 */ ActorListEntry actorLists[ACTORCAT_COUNT];
} ActorContext; // size = 0xA0 (at least)

typedef struct PlayState {
    /* 0x0000 */ char unk_0000[0x30];
    /* 0x0030 */ uint32_t buttonsHeld; // pad bits; bit 12 passes through from the pad
    /* 0x0034 */ uint32_t buttonsPressed; // pressed this frame; bit 3 is Start
    /* 0x0038 */ char unk_0038[0x110];
    /* 0x0148 */ int16_t sceneNum;
    /* 0x014A */ char unk_014A[0xD6];
    /* 0x0220 */ Vec3f viewEye; // where the frame is drawn from (docs/actors.md)
    /* 0x022C */ Vec3f viewAt; // and the point it looks at
    /* 0x0238 */ char unk_0238[0x1E78];
    /* 0x20B0 */ ActorContext actorCtx;
    /* 0x2150 */ char unk_2150[0x2D8];
    /* 0x2428 */ CutsceneContext csCtx;
    /* 0x2690 */ char unk_2690[0x5990];
    /* 0x8020 */ char msgCtx[0x4509];
    /* 0xC529 */ int8_t transitionTrigger; // 20 requests a scene transition
    /* 0xC52A */ char unk_C52A[0x4];
    /* 0xC52E */ int16_t nextEntrance;
} PlayState;

// CommonData.hudVisibility (docs/ui.md); the names are the N64 game's.
#define HUD_VISIBILITY_NONE 1
#define HUD_VISIBILITY_NONE_ALT 2
#define HUD_VISIBILITY_ALL 50

// The touch screen's screens (docs/ui.md); the values index gUiScreens.
#define UI_SCREEN_BLACK 0
#define UI_SCREEN_MAIN 1
#define UI_SCREEN_GEAR 3
#define UI_SCREEN_ITEMS 4
#define UI_SCREEN_MAP 5
#define UI_SCREEN_MASKS 6
#define UI_SCREEN_OCARINA 7
#define UI_SCREEN_COUNT 8

typedef struct UiScreenContext {
    /* 0x00 */ void* vtable;
    /* 0x04 */ char unk_04[0x4];
    /* 0x08 */ void* activeScreen; // the gUiScreens entry that is up
    /* 0x0C */ char unk_0C[0x4];
} UiScreenContext; // size = 0x10 (at least)

// BgCheck_Allocate's budget for a scene's static collision (docs/formats/scene_files.md).
#define BGCHECK_SUBDIV_OVERLAP 50
#define BGCHECK_SUBDIV_MIN 150
#define BGCHECK_LOOKUP_SIZE 6
#define BGCHECK_SSNODE_SIZE 4
#define BGCHECK_SSNODE_NULL 0xFFFF
#define BGCHECK_POLY_ID_MAX 0x7FFF
#define BGCHECK_DYNA_POLY_SIZE 20
#define BGCHECK_DYNA_VTX_SIZE 6
#define BGCHECK_CONTEXT_SIZE 0x1600
#define BGCHECK_MEMSIZE 0x40000
// The scenes of sBgCheckSpotScenes.
#define BGCHECK_SPOT_SUBDIV_XZ 32
#define BGCHECK_SPOT_SUBDIV_Y 8
#define BGCHECK_SPOT_DYNA_NODES 1000
#define BGCHECK_SPOT_DYNA_POLYS 512
#define BGCHECK_SPOT_DYNA_VTX 512
// Every other scene; sBgCheckSceneDyna and sBgCheckSceneSubdiv name the exceptions.
#define BGCHECK_SUBDIV_XZ 16
#define BGCHECK_SUBDIV_Y 4
#define BGCHECK_DYNA_NODES 1000
#define BGCHECK_DYNA_POLYS 600
#define BGCHECK_DYNA_VTX 600

#define BGCHECK_SPOT_SCENE_COUNT 1
#define BGCHECK_SCENE_DYNA_COUNT 1
#define BGCHECK_SCENE_SUBDIV_COUNT 3

typedef struct BgCheckSceneDyna {
    /* 0x00 */ int16_t sceneId;
    /* 0x02 */ int16_t polyNodesMax;
    /* 0x04 */ int16_t polyListMax;
    /* 0x06 */ int16_t vtxListMax;
} BgCheckSceneDyna; // size = 0x8

typedef struct BgCheckSceneSubdiv {
    /* 0x00 */ int16_t sceneId;
    /* 0x02 */ int16_t subdivAmount[3];
    /* 0x08 */ int32_t nodeListMax;
} BgCheckSceneSubdiv; // size = 0xC

extern int16_t sBgCheckSpotScenes[BGCHECK_SPOT_SCENE_COUNT]; // 0x0065C330
extern BgCheckSceneDyna sBgCheckSceneDyna[BGCHECK_SCENE_DYNA_COUNT]; // 0x0065C332
extern BgCheckSceneSubdiv sBgCheckSceneSubdiv[BGCHECK_SCENE_SUBDIV_COUNT]; // 0x0065C3EC

// Scene files by scene id.
#define SCENE_TABLE_COUNT 117

typedef struct SceneTableEntry {
    /* 0x00 */ char unk_00[0x8];
    /* 0x08 */ char infoPath[0x34];
    /* 0x3C */ char archivePath[0x34];
} SceneTableEntry; // size = 0x70

extern SceneTableEntry gSceneTable[SCENE_TABLE_COUNT]; // 0x0069B340

// SaveData.upgrades: the wallet, 0 holds 99 rupees and 1 holds 200.
#define UPGRADE_WALLET_SHIFT 12
#define UPGRADE_WALLET_MASK 0x3000
#define BUTTON_ENABLED 0
#define BUTTON_DISABLED 0xFF

// A node of a layout's tree (docs/hud.md).
#define UI_WIDGET_VISIBLE 0x1 // flags
#define UI_WIDGET_VISIBLE_CHANGED 0x20000 // flags: set by a change; activeFlags: set while visible
#define UI_WIDGET_FLAGS_HIDDEN 0x0FFFFF0E
#define UI_WIDGET_ACTIVE_FLAGS_HIDDEN 0x0FFDFF00

typedef struct UiWidget {
    /* 0x000 */ char unk_000[0x20];
    /* 0x020 */ struct UiLayout* layout; // the layout a widget stands for, or NULL
    /* 0x024 */ char unk_024[0x5C];
    /* 0x080 */ float alpha;
    /* 0x084 */ uint32_t flags; // UI_WIDGET_*
    /* 0x088 */ uint32_t activeFlags;
    /* 0x08C */ char unk_08C[0xB0];
} UiWidget; // size = 0x13C

typedef struct UiLayout {
    /* 0x000 */ void* vtable;
    /* 0x004 */ void* layoutClass;
    /* 0x008 */ UiWidget root;
    /* 0x144 */ char unk_144[0x2C];
} UiLayout; // size = 0x170

// Joker.Main.Play.AActionIcon and BActionIcon.
typedef struct PlayActionIcon {
    /* 0x000 */ UiLayout layout;
    /* 0x170 */ char unk_170[0x20];
    /* 0x190 */ uint16_t textNum; // the label shown
} PlayActionIcon; // size = 0x194 (at least)

// Joker.Main.Play.Hud: the top screen's clock and action buttons.
typedef struct PlayHud {
    /* 0x000 */ UiLayout layout;
    /* 0x170 */ UiWidget* chatAlert;
    /* 0x174 */ UiWidget* eventTimer;
    /* 0x178 */ UiWidget* gyroGroup;
    /* 0x17C */ UiWidget* shootingFrame;
    /* 0x180 */ UiWidget* aActionButton;
    /* 0x184 */ UiWidget* bActionButton;
    /* 0x188 */ char unk_188[0x20];
    /* 0x1A8 */ PlayActionIcon* aActionIcon;
    /* 0x1AC */ PlayActionIcon* bActionIcon;
    /* 0x1B0 */ char unk_1B0[0x80];
    /* 0x230 */ float opacity; // set every frame; PlayHud_Draw draws nothing at 0
} PlayHud; // size = 0x234 (at least)

// gUiCommonLayouts.
#define UI_LAYOUT_TOUCH_PANEL 0 // Joker.Main.Play.TouchPanel: the main touch screen's HUD
#define UI_LAYOUT_BACKGROUND 1
#define UI_LAYOUT_HUD 2 // PlayHud
#define UI_LAYOUT_COUNT 49

// sItemIconFrames: no icon.
#define ITEM_ICON_NONE 0xFF
#define ITEM_ICON_COUNT 0xA0

// The game's view of the gyroscope (docs/motion.md). Angles are degrees since the last reset.
typedef struct MotionState {
    /* 0x00 */ void* reader; // the SDK's GyroscopeReader, GYRO_READER_*
    /* 0x04 */ float pitch;
    /* 0x08 */ float yaw;
    /* 0x0C */ float roll; // always 0
    /* 0x10 */ float direction[3]; // pitch, yaw, roll of the reader's direction matrix
    /* 0x1C */ float unwrapped[3];
    /* 0x28 */ float previous[3];
    /* 0x34 */ float reference[3];
    /* 0x40 */ float yawScale; // 2.1: view degrees per degree of the 3DS
    /* 0x44 */ float pitchScale; // 1.46
    /* 0x48 */ uint8_t reset; // asks Motion_Update for a new reference
    /* 0x49 */ uint8_t resetDone; // for the frame the reference was taken
    /* 0x4A */ uint8_t valid;
} MotionState; // size = 0x4C

// MotionState.reader. Speeds are in units of 360 degrees a second.
#define GYRO_READER_SPEED 0x7E0 // float[3]
#define GYRO_READER_ANGLE 0x7EC // float[3], turns
#define GYRO_READER_DIRECTION 0x7F8 // float[9], rows are the 3DS's axes
#define GYRO_READER_ZERO_PLAY_ON 0x854 // u8
#define GYRO_READER_ZERO_DRIFT_ON 0x855 // u8
#define GYRO_READER_REVISE_ON 0x856 // u8: the accelerometer pulls the direction toward gravity
#define GYRO_READER_ZERO_PLAY 0x858 // float
#define GYRO_READER_DRIFT_BIAS 0x8A0 // float[3], raw units

// The player's look in first person and with an aimed item (Player_UpdateLook).
#define PLAYER_STATE_FLAGS_1 0x11DB0 // u32
#define PLAYER_STATE1_FIRST_PERSON 0x100000
#define PLAYER_LOOK_BASE 0x125B8 // s16[3]: focus.rot at the last motion reset
#define PLAYER_LOOK_FLAGS 0x129BC // u32: bit 0, the gyroscope sets focus.rot
#define PLAYER_PAD 0x129CC // pointer to the pad state the player reads

extern MotionState gMotionState; // 0x006B1DF4
extern UiLayout* gUiCommonLayouts[UI_LAYOUT_COUNT]; // 0x006B7B8C
extern uint8_t sItemIconFrames[ITEM_ICON_COUNT]; // 0x006562F0
extern CommonData gCommonData; // 0x007751D8
extern PlayState* gPlayState; // 0x00667890
extern UiScreenContext gUiScreenContext; // 0x0072F5BC
extern void* gUiScreens[UI_SCREEN_COUNT]; // 0x00656B00

#endif
