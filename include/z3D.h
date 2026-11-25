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
#define ITEM_OCARINA 0x00
#define ITEM_BOW 0x01
#define ITEM_ARROW_FIRE 0x02
#define ITEM_ARROW_ICE 0x03
#define ITEM_ARROW_LIGHT 0x04
#define ITEM_BOMB 0x06
#define ITEM_BOMBCHU 0x07
#define ITEM_DEKU_STICK 0x08
#define ITEM_DEKU_NUT 0x09
#define ITEM_MAGIC_BEANS 0x0A
#define ITEM_POWDER_KEG 0x0C
#define ITEM_PICTOGRAPH_BOX 0x0D
#define ITEM_BOTTLE 0x12 // empty
#define ITEM_MASK_BUNNY 0x39
#define ITEM_NONE 0xFF
#define SLOT_OCARINA 0 // SaveData.items
#define SLOT_BOW 1
#define SLOT_BOMB 6
#define SLOT_PICTOGRAPH_BOX 13
#define MASK_SLOTS_FIRST 24
#define SLOT_MASK_BUNNY 32
#define BOTTLE_SLOTS_FIRST 48
#define INVENTORY_SLOTS 55 // items, masks, then seven bottles (docs/items.md)
// PlayState.buttonsHeld: the HID module's debug bit, which no 3DS button sets.
#define PAD_DEBUG 0x1000
// The item buttons the pad has, and with them the ocarina's five notes from low to high: L, R, Y,
// X, A (docs/ocarina.md).
#define PAD_A 0x1
#define PAD_SELECT 0x4
#define PAD_R 0x100
#define PAD_L 0x200
#define PAD_X 0x400
#define PAD_Y 0x800
// gTouchButtonsHeld and gTouchButtonsPressed: the main touch screen's item buttons.
#define TOUCH_BUTTON_I 0x1
#define TOUCH_BUTTON_II 0x2
#define TOUCH_BUTTON_OCARINA 0x8
#define PLAYER_FORM_HUMAN 4
#define SCENES_VISIBLE_WORDS 7

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
    /* 0x01F0 */ uint32_t questItems; // QUEST_*; bit 18: the Bombers' Notebook
    /* 0x01F4 */ uint8_t dungeonItems[10];
    /* 0x01FE */ int8_t dungeonKeys[9]; // by DUNGEON_INDEX_*; -1 none yet
    /* 0x0207 */ char unk_0207[0xFE1];
    /* 0x11E8 */ uint32_t scenesVisible[SCENES_VISIBLE_WORDS]; // a scene's map in play and on the Map screen: bit sceneNum % 32 of word sceneNum / 32 (Tingle's maps)
    /* 0x1204 */ char unk_1204[0x44];
    /* 0x1248 */ uint8_t weekEventReg[100]; // flag n is byte n / 8, bit n % 8
    /* 0x12AC */ char unk_12AC[0x77C];
    /* 0x1A28 */ uint8_t itemGrid[20]; // the Items screen's cells, five to a row: an inventory slot
    /* 0x1A3C */ uint8_t maskGrid[24]; // the Masks screen's cells, six to a row
    /* 0x1A54 */ char unk_1A54[0x34];
} SaveData; // size = 0x1A88

// The final hours: from midnight of the last day, SaveData.day, until the moon falls at dawn.
#define FINAL_DAY 3
#define CLOCK_TIME_DAWN 0x4000

// SaveData.questItems: the songs, in the song table's order from the Sonata of Awakening; the
// Song of Time is the seventh. The Goron Lullaby's intro has its own bit.
#define QUEST_SONG_FIRST 6
#define QUEST_SONG_COUNT 12
#define QUEST_SONG_LULLABY_INTRO 24
#define QUEST_BOMBERS_NOTEBOOK 18
#define WEEK_EVENT_REGION_MAPS 0x23 // weekEventReg byte: bit n owns region n's map, the Map screen's loupe (docs/ui.md)
#define REGION_MAP_COUNT 6

// Where and how the player comes back into a scene (docs/save.md, "Respawn").
typedef struct RespawnData {
    /* 0x00 */ float pos[3];
    /* 0x0C */ int16_t yaw;
    /* 0x0E */ int16_t playerParams; // 0x0DFF at South Clock Town's owl statue
    /* 0x10 */ uint16_t entrance;
    /* 0x12 */ uint8_t room; // the room the scene loads first
    /* 0x13 */ char unk_13[0xD];
} RespawnData; // size = 0x20

#define RESPAWN_COUNT 8

// The camera options' choices, in the order the Options screen steps through them.
#define CAMERA_INVERT_NONE 0
#define CAMERA_INVERT_Y 1
#define CAMERA_INVERT_X 2
#define CAMERA_INVERT_BOTH 3
#define VOLUME_LOWER 0
#define VOLUME_NORMAL 1
#define VOLUME_HIGHER 2

typedef struct CommonData {
    /* 0x00000 */ char unk_00000[0x8]; // start and scene
    /* 0x00008 */ SaveData save;
    /* 0x01A90 */ char unk_01A90[0x1A88];
    /* 0x03518 */ uint32_t entrance; // the scene's entrance in play; on load, where the file starts
    /* 0x0351C */ uint16_t statueEntrance; // where a statue save loads (docs/save.md)
    /* 0x0351E */ uint8_t statueSave; // the file was saved at a statue: its load resumes the cycle
    /* 0x0351F */ uint8_t targetHold; // the L-Targeting option: 1 Hold, 0 Switch (docs/ui.md "Options")
    /* 0x03520 */ uint8_t motionOff; // the Motion Controls option: 0 is on (docs/motion.md)
    /* 0x03521 */ uint8_t circlePadPro; // the Circle Pad Pro option: 1 Use; 0 also turns the free camera off
    /* 0x03522 */ char unk_03522[0x2];
    /* 0x03524 */ uint8_t firstPersonInvert; // the First-Person Camera option: CAMERA_INVERT_*
    /* 0x03525 */ char unk_03525[0x7];
    /* 0x0352C */ uint8_t swimInvert; // the Swimming Controls option: 1 inverts up and down
    /* 0x0352D */ uint8_t freeCameraInvert; // the Free Camera option: CAMERA_INVERT_*
    /* 0x0352E */ uint8_t volume; // the Adjust Volume option: VOLUME_*, applied by Audio_SetVolumeSetting
    /* 0x0352F */ char unk_0352F[0x100ED];
    /* 0x1361C */ int32_t setup; // 1 on the title screen, 0 in play
    /* 0x13620 */ char unk_13620[0x4];
    /* 0x13624 */ int32_t respawnFlag; // n > 0: the next scene load starts from respawn[n - 1], then it is 0
    /* 0x13628 */ RespawnData respawn[RESPAWN_COUNT];
    /* 0x13728 */ char unk_13728[0x18];
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

// Command 90's camera (docs/cutscene.md "The camera's shots"): CutsceneCamera_UpdateSplines
// (0x1AD820) steps an interpolator for the eye and one for at through the command's points, a
// group of points (a shot) at a time.
typedef struct {
    /* 0x00 */ char unk_00[0x4];
    /* 0x04 */ int16_t curFrame;
    /* 0x06 */ int16_t waypoint; // in the group
    /* 0x08 */ int16_t groupCount; // the group's points
    /* 0x0A */ int16_t numEntries;
    /* 0x0C */ uint8_t group; // the group's first point
    /* 0x0D */ uint8_t type; // the group's interpolation; CS_CAM_GROUP_PENDING until it is read
    /* 0x0E */ char unk_0E[0xBA];
} CutsceneCameraInterp; // size = 0xC8

#define CS_CAM_GROUP_PENDING 8

typedef struct {
    /* 0x00 */ int16_t splineIndex;
    /* 0x02 */ int16_t cmdIndex; // the next spline's offset in the command's data
    /* 0x04 */ int16_t splineNeedsInit;
    /* 0x06 */ int16_t state;
    /* 0x08 */ int16_t nextSplineTimer;
    /* 0x0A */ int16_t updateSplineTimer;
    /* 0x0C */ int16_t duration;
    /* 0x0E */ char unk_0E[0x22];
    /* 0x30 */ CutsceneCameraInterp eyeInterp;
    /* 0xF8 */ CutsceneCameraInterp atInterp;
} CutsceneCamera; // size = 0x1C0 (at least)

extern CutsceneCamera sCutsceneCameraInfo; // 0x0078A8A4
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

// How an actor's model is placed (docs/actors.md); the N64 game's ActorShape, as far as it is read.
typedef struct ActorShape {
    /* 0x0 */ int16_t rot[3]; // the model's rotation; the player's yaw follows world.rot's
} ActorShape; // size = 0x6 (at least)

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
    /* 0x07C */ char unk_07C[0x44];
    /* 0x0C0 */ ActorShape shape;
    /* 0x0C6 */ char unk_0C6[0x46];
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

// One limb's pose relative to its parent, as the update leaves it (docs/actors.md "Skeletons").
typedef struct SkelJoint {
    /* 0x00 */ float mtx[3][4];
    /* 0x30 */ uint32_t unk_30;
} SkelJoint; // size = 0x34

// An actor's skeleton (docs/actors.md "Skeletons"); the player's is at +0x334.
typedef struct SkelAnime {
    /* 0x00 */ char unk_00[0x34];
    /* 0x34 */ void* model; // what SkelAnime_DrawOpa queues
    /* 0x38 */ char unk_38[0x44];
    /* 0x7C */ uint8_t limbCount;
    /* 0x7D */ char unk_7D[0x3];
    /* 0x80 */ SkelJoint* jointTable; // limbCount joints, posed in the update, read by the draw
    /* 0x84 */ SkelJoint* unk_84; // a second joint table
} SkelAnime; // size = 0x88 (at least)

// The calls that queue a skeleton's model (r1 the SkelAnime), from the start of SkelAnime_DrawOpa
// and of SkelAnime_DrawOpaEx, which takes one more word from its caller.
#define SKELANIME_DRAW_OPA_QUEUE_CALL 0x48
#define SKELANIME_DRAW_OPA_EX_QUEUE_CALL 0x40

#define ACTORCAT_PLAYER 2
#define ACTORCAT_COUNT 12

// A CMAB material animation's file (docs/frame.md "Material animations"): the animation's block at
// `animOffset` from its start.
typedef struct CmabHeader {
    /* 0x00 */ char magic[4]; // "cmab"
    /* 0x04 */ char unk_04[0x10];
    /* 0x14 */ uint32_t animOffset;
} CmabHeader;

typedef struct CmabAnim {
    /* 0x0 */ int32_t unk_0;
    /* 0x4 */ int32_t frameCount; // AnimPlayer_Step wraps or holds the frame here
} CmabAnim;

// A loaded CMAB, as an AnimPlayer holds it.
typedef struct CmabResource {
    /* 0x0 */ void* vtable;
    /* 0x4 */ CmabHeader* file;
} CmabResource;

// A material animation playing on a model (docs/frame.md "Material animations"), vtable 0x63BF00.
// AnimPlayer_Step adds `speed` to `frame`, wraps it at the animation's frame count when `loop` is
// set and holds it at the end otherwise; AnimPlayer_Update steps it when `autoStep` is set, then
// applies the frame to each target.
typedef struct AnimPlayer {
    /* 0x00 */ void* vtable;
    /* 0x04 */ char unk_04[0x4];
    /* 0x08 */ void* model;
    /* 0x0C */ CmabResource* anim;
    /* 0x10 */ float frame;
    /* 0x14 */ float speed;
    /* 0x18 */ uint8_t loop;
    /* 0x19 */ uint8_t paused; // no step while set, nor while its group's bit is in 0x6A3A18
    /* 0x1A */ uint8_t done; // the frame reached the end
    /* 0x1B */ uint8_t autoStep;
    /* 0x1C */ uint8_t group;
    /* 0x1D */ char unk_1D[0x3];
    /* 0x20 */ void* targets[32];
    /* 0xA0 */ int32_t targetCount;
} AnimPlayer; // size = 0xA4

// A model's material animations, updated together by AnimPlayerList_Update.
typedef struct AnimPlayerList {
    /* 0x0 */ uint16_t count;
    /* 0x2 */ char unk_2[0x2];
    /* 0x4 */ AnimPlayer* players; // `count` of them
} AnimPlayerList;

// AnimPlayerList_Update's call of each player's AnimPlayer_Update (r0 the player), from its start.
#define ANIM_PLAYER_LIST_UPDATE_CALL 0x30
// Model_Update's call of its material animation's update through the player's vtable (r0 the
// player at the model's +0x98, r1 the method: AnimPlayer_Update for an AnimPlayer), from its start.
#define MODEL_UPDATE_MATERIAL_CALL 0x58

typedef struct ActorContext {
    /* 0x00 */ char unk_00[0x10];
    /* 0x10 */ ActorListEntry actorLists[ACTORCAT_COUNT];
} ActorContext; // size = 0xA0 (at least)

// A point seen from another (OLib_Vec3fDiffToVecGeo): pitch is the elevation, so positive is above.
typedef struct VecGeo {
    /* 0x0 */ float r;
    /* 0x4 */ int16_t pitch;
    /* 0x6 */ int16_t yaw;
} VecGeo; // size = 0x8

struct PlayState;

// A camera (docs/camera.md). Camera_Follow reads the eye back from eyeNext every update, so a turn
// of eyeNext around at is kept.
typedef struct Camera {
    /* 0x000 */ char unk_000[0x14];
    /* 0x014 */ int16_t yawRate; // Camera_Follow: the C-stick's turn this update, eased
    /* 0x016 */ int16_t pitchRate;
    /* 0x018 */ char unk_018[0x38];
    /* 0x050 */ Vec3f at;
    /* 0x05C */ Vec3f eye; // after collision
    /* 0x068 */ char unk_068[0xC];
    /* 0x074 */ Vec3f eyeNext; // before collision
    /* 0x080 */ char unk_080[0x20];
    /* 0x0A0 */ struct PlayState* play;
    /* 0x0A4 */ char unk_0A4[0xB2];
    /* 0x156 */ int16_t setting; // an index of sCameraSettings
    /* 0x158 */ int16_t mode; // an index of the setting's cameraModes
    /* 0x15A */ char unk_15A[0x18];
    /* 0x172 */ int16_t animState; // the camera function's step
    /* 0x174 */ char unk_174[0x24];
} Camera; // size = 0x198

// Indices into sCameraFunctions (0x667D38), in the N64 order.
#define CAM_FUNC_SPEC9 70 // Camera_Special9 (0x470818), the room door camera

// Camera_Special9's animState when it has moved the eye to the door's far side.
#define CAM_SPEC9_ANIM_FAR_SIDE 2

// Camera_Update (0x180CC4) runs sCameraFunctions[sCameraSettings[setting].cameraModes[mode].funcIdx].
typedef struct {
    /* 0x00 */ int16_t funcIdx;
    /* 0x02 */ int16_t valueCnt;
    /* 0x04 */ void* values;
} CameraMode; // size = 0x8

typedef struct {
    /* 0x00 */ char unk_00[0x8];
    /* 0x08 */ CameraMode* cameraModes;
} CameraSetting; // size = 0xC

extern CameraSetting sCameraSettings[]; // 0x00667894

// The view the frame is drawn from (docs/camera.md "The view"), the N64 game's layout as far as
// it is known. Camera_Update ends with View_LookAt (0x184618) writing eye, at and up.
typedef struct View {
    /* 0x00 */ char unk_00[0x18];
    /* 0x18 */ float fovy; // degrees
    /* 0x1C */ float zNear;
    /* 0x20 */ float zFar;
    /* 0x24 */ float scale;
    /* 0x28 */ Vec3f eye;
    /* 0x34 */ Vec3f at;
    /* 0x40 */ Vec3f up;
} View; // size = 0x4C (at least)

#define CAMERA_COUNT 4

// Writes a built file to save<n>.bin as a job; SaveFile_UpdateWrite frees the job once done.
typedef struct SaveWriter {
    /* 0x00 */ void* job;
    /* 0x04 */ char unk_04[0x4];
    /* 0x08 */ void* buffer; // the file's 0x13618 bytes
    /* 0x0C */ char unk_0C[0x4];
    /* 0x10 */ int16_t state; // SAVE_WRITER_*
    /* 0x12 */ char unk_12[0x2];
} SaveWriter; // size = 0x14

#define SAVE_WRITER_IDLE 0
#define SAVE_WRITER_WRITING 2
// An entrance is scene << 9 | spawn << 4 | layer; a statue's entrance has layer 0.
#define ENTRANCE_LAYER_MASK 0xF

// A screen fill faded in or out (docs/frame.md "Fades"), OoT3D's layout.
typedef struct {
    /* 0x0 */ uint8_t type;
    /* 0x1 */ uint8_t isDone;
    /* 0x2 */ uint8_t direction;
    /* 0x3 */ char unk_3;
    /* 0x4 */ uint8_t a; // the fill's colour, alpha first; TransitionFade_Draw skips a fill with alpha 0
    /* 0x5 */ uint8_t b;
    /* 0x6 */ uint8_t g;
    /* 0x7 */ uint8_t r;
    /* 0x8 */ uint16_t timer;
    /* 0xA */ char unk_A[0x2];
} TransitionFade; // size = 0xC

// The scene transition (docs/frame.md "Fades"): its instance, a TransitionFade while `draw` is
// TransitionFade_Draw.
typedef struct {
    /* 0x000 */ union {
        TransitionFade fade;
        char data[0x234];
    } instanceData;
    /* 0x234 */ void* draw; // void (*)(void* instance)
} TransitionContext; // size = 0x238 (at least)

typedef struct PlayState {
    /* 0x0000 */ char unk_0000[0x30];
    /* 0x0030 */ uint32_t buttonsHeld; // pad bits; bit 12 passes through from the pad
    /* 0x0034 */ uint32_t buttonsPressed; // pressed this frame; bit 3 is Start
    /* 0x0038 */ char unk_0038[0x100];
    /* 0x0138 */ uint32_t frames; // the game state's ticks (counted by 0x10676C), from 0 again in a new scene
    /* 0x013C */ char unk_013C[0xC];
    /* 0x0148 */ int16_t sceneNum;
    /* 0x014A */ char unk_014A[0xAE];
    /* 0x01F8 */ View view; // the eye is where the frame is drawn from (docs/actors.md)
    /* 0x0244 */ char unk_0244[0x1C4];
    /* 0x0408 */ Camera mainCamera;
    /* 0x05A0 */ char unk_05A0[0x4C8];
    /* 0x0A68 */ Camera* cameraPtrs[CAMERA_COUNT]; // the main camera first
    /* 0x0A78 */ int16_t activeCamera; // the index of the camera the view follows
    /* 0x0A7A */ char unk_0A7A[0x1636];
    /* 0x20B0 */ ActorContext actorCtx;
    /* 0x2150 */ char unk_2150[0x2D8];
    /* 0x2428 */ CutsceneContext csCtx;
    /* 0x2690 */ char unk_2690[0x155C];
    /* 0x3BEC */ SaveWriter saveWriter; // a statue's save (docs/save.md)
    /* 0x3C00 */ char unk_3C00[0x4420];
    /* 0x8020 */ char msgCtx[0x62A];
    /* 0x864A */ uint16_t aButtonDoAction; // DO_ACTION_*: the A button's word (docs/hud.md)
    /* 0x864C */ char unk_864C[0x26];
    /* 0x8672 */ int16_t aButtonAlpha; // PlayActionIcon_Update fades the A button toward it; not run
    /* 0x8674 */ char unk_8674[0x3BEC];
    /* 0xC260 */ int8_t roomNum; // the room in play
    /* 0xC261 */ char unk_C261[0x2C8];
    /* 0xC529 */ int8_t transitionTrigger; // 20 requests a scene transition
    /* 0xC52A */ char unk_C52A[0x4];
    /* 0xC52E */ int16_t nextEntrance;
    /* 0xC530 */ char unk_C530[0x32A];
    /* 0xC85A */ uint8_t transitionMode; // Play_Draw draws transitionCtx in 3 and 0xB
    /* 0xC85B */ char unk_C85B[0x5];
    /* 0xC860 */ TransitionContext transitionCtx;
    /* 0xCA98 */ char unk_CA98[0x14];
    /* 0xCAAC */ TransitionFade transitionFadeFlash; // drawn by TransitionFade_Draw after the transition
} PlayState;

// Play_Main's call of Play_Draw (docs/frame.md), from the function's start.
#define PLAY_MAIN_DRAW_CALL 0x160
// Graph_DrawFrame's call of the frame end (Graph_FrameEnd, docs/frame.md), from its start.
#define GRAPH_DRAW_FRAME_END_CALL 0xA04
// Target_Draw's turn of the arrow (docs/actors.md "The target arrow"), from its start: the angle
// moved to s0, then made a float.
#define TARGET_DRAW_ARROW_TURN_MOVE 0x814
#define TARGET_DRAW_ARROW_TURN_CONVERT 0x820
// The arrow's turn each tick, in binary angles.
#define TARGET_ARROW_TURN_STEP 3000

// nn::gx's command list (docs/frame.md), OoT3D's layout: a buffer of PICA commands and the
// requests the frame end hands the GSP in order.
typedef struct {
    /* 0x00 */ uint32_t type; // the GSP GX command it becomes (docs/frame.md "Requests"), in the low byte
    /* 0x04 */ uint32_t args[6]; // nngx's encoding of its parameters, not the GSP command's
} GxRequest; // size = 0x1C

typedef struct {
    /* 0x00 */ uint32_t unk_00;
    /* 0x04 */ uint32_t buffer;
    /* 0x08 */ uint32_t bufferSize;
    /* 0x0C */ uint32_t usedBytes;
    /* 0x10 */ char unk_10[0x8];
    /* 0x18 */ GxRequest* requests;
    /* 0x1C */ uint32_t requestCapacity;
    /* 0x20 */ uint32_t requestCount;
    /* 0x24 */ char unk_24[0x20];
} GxCmdlist; // size = 0x44

typedef struct {
    /* 0x00 */ char unk_00[0x9C];
    /* 0x9C */ GxCmdlist* boundCmdlist; // the list nngxBindCmdlist (0x136A1C) bound, which draws append to
} NngxState;
extern NngxState gNngxState; // 0x007B2700

// nn::os::CriticalSection (docs/frame.md "The GSP interrupt lock"): enter 0x192D3C, leave 0x192D9C.
typedef struct {
    /* 0x00 */ int32_t event; // a light event: 1 free, -1 held, one lower for each thread waiting
    /* 0x04 */ uint32_t ownerTls; // the holding thread's TLS address
    /* 0x08 */ uint32_t count; // the holder's nested entries
} OsCriticalSection; // size = 0xC

// nngx's GSP interrupt dispatcher's lock, which its interrupt thread holds while it runs a callback.
extern OsCriticalSection gGspInterruptLock; // 0x007C0F50

// CommonData.hudVisibility (docs/ui.md); the names are the N64 game's.
#define HUD_VISIBILITY_NONE 1
#define HUD_VISIBILITY_NONE_ALT 2
#define HUD_VISIBILITY_ALL 50

// The touch screen's screens (docs/ui.md); the values index gUiScreens.
#define UI_SCREEN_BLACK 0
#define UI_SCREEN_MAIN 1
#define UI_SCREEN_SCHEDULE 2 // the Bombers' Notebook
#define UI_SCREEN_GEAR 3
#define UI_SCREEN_ITEMS 4
#define UI_SCREEN_MAP 5
#define UI_SCREEN_MASKS 6
#define UI_SCREEN_OCARINA 7
#define UI_SCREEN_COUNT 8

// A screen's prompts over the touch screen (vtable 0x63CA00): the window, its buttons, and the
// black that dims the screen behind it (docs/ui.md "Title and file select").
typedef struct UiDialogLayout {
    /* 0x000 */ char unk_000[0x3B4];
    /* 0x3B4 */ struct UiWidget* window; // window_g
    /* 0x3B8 */ char unk_3B8[0x3C];
    /* 0x3F4 */ struct UiWidget* blackScreen; // black_screen_g, the touch screen's 320x240 from its top left
} UiDialogLayout; // size = 0x3F8 (at least)

// File select's list on the touch screen (vtable 0x63C7F4). Its groups and panes are found by name
// (UiLayout_FindWidget): start_g holds the Start page's btn_start_g, btn_copy_g, btn_delete_g and
// btn_option_g, each with bb_* panes holding its touch rect on screen as last drawn (left, top,
// right, bottom floats at +0x2C), what the game hit-tests; cursor_g holds
// their glows, cursor_start_g, cursor_copy_del_g (Copy's and Erase's) and cursor_option_g.
typedef struct FileSelectList {
    /* 0x000 */ char unk_000[0x6E4];
    /* 0x6E4 */ struct UiWidget* returnButton; // btn_return_l, at (0, 202)
} FileSelectList; // size = 0x6E8 (at least)

// The title's screen (docs/ui.md "Title and file select"): TitleScreen_Draw queues pressStart.
typedef struct TitleScreen {
    /* 0x00 */ char unk_00[0x8];
    /* 0x08 */ struct UiLayout* pressStart; // PRESS START, queue 5
    /* 0x0C */ char unk_0C[0x10];
    /* 0x1C */ struct UiLayout* touchBackground; // queue 4
} TitleScreen; // size = 0x20 (at least)

// File select's screen: FileSelectScreen_Draw queues each layout it holds.
typedef struct FileSelectScreen {
    /* 0x000 */ char unk_00[0x1C];
    /* 0x1C */ FileSelectList* files; // the touch screen's list, the file's Start, Copy and Erase, Return; queue 5
    /* 0x20 */ struct UiLayout* touchBackground; // queue 4
    /* 0x24 */ struct UiLayout* details; // the top screen's plate of the file under the cursor; queue 2
    /* 0x28 */ struct UiLayout* topBackground; // queue 0
    /* 0x2C */ struct UiLayout* titleBar; // "Select File" and the clock; queue 2
    /* 0x30 */ UiDialogLayout* dialogs; // the touch screen's prompts ("Saving...", yes and no); queue 5
    /* 0x34 */ char unk_34[0x588];
    /* 0x5BC */ uint8_t page; // FILE_SELECT_PAGE_*, set once the slide to it ends
    /* 0x5BD */ uint8_t nextPage; // the page being slid to, or page
    /* 0x5BE */ char unk_5BE[0xA];
    /* 0x5C8 */ int32_t startChoice; // FILE_START_CHOICE_*: the Start page's button under the cursor
} FileSelectScreen; // size = 0x5CC (at least)
#define FILE_SELECT_PAGE_FILES 0
#define FILE_SELECT_PAGE_START 1 // the file's Start, Copy, Erase and Options
#define FILE_SELECT_PAGE_COPY 2
#define FILE_START_CHOICE_START 0
#define FILE_START_CHOICE_COPY 1
#define FILE_START_CHOICE_OPTIONS 2
#define FILE_START_CHOICE_ERASE 3
// How far the cursor animation moves cursor_copy_del_g from Copy to Erase: their distance.
#define FILE_START_ERASE_CURSOR_SHIFT 104
// File select's Options screen: OptionsScreen_Draw queues each layout it holds; the function at
// 0x5A1E2C puts the cursor's root at its place for the plate chosen.
#define OPTIONS_CURSOR_PLACES 8
typedef struct OptionsScreen {
    /* 0x000 */ char unk_00[0xA];
    /* 0x00A */ uint8_t choice; // the plate chosen, an index of cursorPlaces
    /* 0x00B */ char unk_0B[0x5];
    /* 0x10 */ struct UiLayout* list; // the touch screen's option plates on two pages, their tabs, Return; queue 5
    /* 0x14 */ struct UiLayout* touchBackground; // queue 4
    /* 0x18 */ struct UiLayout* cursor; // the frame on the plate chosen, its root moved there; queue 5
    /* 0x1C */ struct UiLayout* topBackground; // queue 0
    /* 0x20 */ struct UiLayout* titleBar; // "Options" with the clock; queue 2
    /* 0x24 */ char unk_24[0x128];
    /* 0x14C */ Vec3f cursorPlaces[OPTIONS_CURSOR_PLACES]; // the cursor's root on each plate, both pages
} OptionsScreen; // size = 0x1AC (at least)
// The options' working copies, by plate: L-Targeting, First-Person Camera, Motion Controls,
// Swimming Controls, Adjust Volume, Circle Pad Pro, Free Camera; OptionsScreen_Init reads them from
// gCommonData and OptionsScreen_Commit writes them back.
#define OPTIONS_SCREEN_VALUES 0x13C
#define OPTIONS_SCREEN_VALUE_COUNT 7
// OptionsScreen_Draw's calls of LayoutDrawManager_Draw for the list and the cursor.
#define OPTIONS_SCREEN_DRAW_LIST_CALL 0xA8
#define OPTIONS_SCREEN_DRAW_CURSOR_CALL 0x100
#define OPTIONS_SCREEN_DRAW_TITLE_BAR_CALL 0x140
#define OPTIONS_SCREEN_VTABLE 0x0063A11C
#define OPTIONS_SCREEN_INIT_SLOT 7
// FileSelectScreen's vtable: its build (FileSelectScreen_Init) and its update.
#define FILE_SELECT_SCREEN_VTABLE 0x0063A550
#define FILE_SELECT_SCREEN_INIT_SLOT 7
// FileSelectScreen_Update's call of FileSelectScreen_UpdateStart, from its start.
#define FILE_SELECT_UPDATE_START_CALL 0x580
// Their draws' calls of LayoutDrawManager_Draw, from each function's start: the title's PRESS START
// (a tail call), file select's details, title bar, files and dialogs (a tail call).
#define TITLE_SCREEN_DRAW_PRESS_START_CALL 0x30
#define FILE_SELECT_DRAW_DETAILS_CALL 0x50
#define FILE_SELECT_DRAW_TITLE_BAR_CALL 0x70
#define FILE_SELECT_DRAW_FILES_CALL 0xF8
#define FILE_SELECT_DRAW_DIALOGS_CALL 0x11C

// PICA registers the game writes itself (gPicaCommandNext): a command is the value, then the
// header, the register in its low 16 bits and the bytes to write above.
#define PICA_COMMAND_ALL_BYTES 0x000F0000
#define PICA_REG_SCISSOR_MODE 0x65 // 3 draws only inside
#define PICA_REG_SCISSOR_FROM 0x66 // x | y << 16, the framebuffer's own axes
#define PICA_REG_SCISSOR_TO 0x67
#define PICA_SCISSOR_INSIDE 3
// The target Graph_DrawTopScreen draws into: its framebuffer x runs up the top screen at two
// rows a line, its y leftwards across it; the pass sets its scissor to the whole target.
#define TOP_SCREEN_TARGET_WIDTH 480
#define TOP_SCREEN_TARGET_HEIGHT 400

typedef struct UiScreenContext {
    /* 0x00 */ void* vtable;
    /* 0x04 */ char unk_04[0x4];
    /* 0x08 */ void* activeScreen; // the gUiScreens entry that is up
    /* 0x0C */ void* nextScreen; // the gUiScreens entry to change to, null once changed
} UiScreenContext; // size = 0x10 (at least)

// The Items and Masks screens (gUiScreens[UI_SCREEN_ITEMS] and [UI_SCREEN_MASKS], docs/items.md).
typedef struct ItemScreen {
    /* 0x00 */ char unk_00[0x18];
    /* 0x18 */ int8_t cursorColumn; // buttonColumn on the item buttons' column
    /* 0x19 */ int8_t cursorRow;
    /* 0x1A */ char unk_1A[0x85];
    /* 0x9F */ uint8_t state; // 2 while browsing
    /* 0xA0 */ char unk_A0[0x3];
    /* 0xA3 */ uint8_t buttonColumn; // 5 on Items, 6 on Masks
} ItemScreen; // size = 0xA4 (at least)

// The Ocarina screen (gUiScreens[UI_SCREEN_OCARINA], docs/ocarina.md).
typedef struct OcarinaScreen {
    /* 0x00 */ char unk_00[0x40];
    /* 0x40 */ int32_t playPage; // 1 on "Play your instrument", 0 on the song list
    /* 0x44 */ int32_t songCursor; // the song list's entry, five to a row
} OcarinaScreen; // size = 0x48 (at least)

// gOcarinaListSongs: an entry's value less this is its row of gOcarinaSongButtons.
#define OCARINA_LIST_SONG_BASE 0x12
#define OCARINA_LIST_SONGS 14
#define OCARINA_SONG_BUTTONS_SIZE 9
// A message's text is compiled into elements; the printer shows them over time (docs/message.md).
// An element calls the method of its control code on the printer.
typedef struct MessagePrinterVtbl {
    /* 0x00 */ void* character;
    /* 0x04 */ char unk_04[0x10];
    /* 0x14 */ void* instantOn; // code 0x27
    /* 0x18 */ void* instantOff; // code 0x28
    /* 0x1C */ void* delay; // code 0x29
} MessagePrinterVtbl; // size = 0x78

// The message window's printer (MessageWindow + 0x368).
typedef struct MessagePrinter {
    /* 0x00 */ MessagePrinterVtbl* vtable;
    /* 0x04 */ void* input; // asks the pad; null stops the update
    /* 0x08 */ void* listener;
    /* 0x0C */ void* elements; // the MessageSet being printed
    /* 0x10 */ float speed; // by language: 1 Japanese, 3 the others
    /* 0x14 */ int32_t speedIndex; // code 0x2D; 3 at the start
    /* 0x18 */ float printed; // characters due, in thirtieths
    /* 0x1C */ int32_t element; // the next element
    /* 0x20 */ int32_t character; // the next character in it
    /* 0x24 */ int32_t shown; // characters printed
    /* 0x28 */ char unk_28[0x24];
    /* 0x4C */ float delay; // seconds left of a code 0x29
    /* 0x50 */ uint8_t state; // MESSAGE_PRINTER_*
    /* 0x51 */ char unk_51[0x1];
    /* 0x52 */ uint8_t instant; // the rest of the box prints in this update
    /* 0x53 */ uint8_t choice; // code 0x2F
    /* 0x54 */ char unk_54[0x8];
} MessagePrinter; // size = 0x5C

#define MESSAGE_PRINTER_IDLE 0
#define MESSAGE_PRINTER_PRINTING 1
#define MESSAGE_PRINTER_WAIT_KEY 2 // code 0x31: A for the next box
#define MESSAGE_PRINTER_DELAY 3
#define MESSAGE_PRINTER_END_WAIT 4 // code 0x2B: the message's last box
#define MESSAGE_PRINTER_CHOICE 5
#define MESSAGE_PRINTER_DONE 12

// The message window (gMessageObject): its printer.
#define MESSAGE_WINDOW_PRINTER 0x368

// The message object's ocarina mode word, and its value in free play.
#define MESSAGE_OCARINA_MODE 0x42C
#define MESSAGE_OCARINA_MODE_FREE_PLAY 0xD

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
// SaveData.upgrades' fields, the index into gUpgradeMasks, gUpgradeShifts and gUpgradeCapacities.
#define UPGRADE_QUIVER 0
#define UPGRADE_BOMB_BAG 1
#define UPGRADE_WALLET 4
#define UPGRADE_STICKS 6
#define UPGRADE_NUTS 7
#define UPGRADE_COUNT 8

// SaveData.dungeonKeys' index, and the scenes of each dungeon (PlayState.sceneNum).
#define DUNGEON_INDEX_WOODFALL_TEMPLE 0
#define DUNGEON_INDEX_SNOWHEAD_TEMPLE 1
#define DUNGEON_INDEX_GREAT_BAY_TEMPLE 2
#define DUNGEON_INDEX_STONE_TOWER_TEMPLE 3
#define SCENE_WOODFALL_TEMPLE 0x1B
#define SCENE_SNOWHEAD_TEMPLE 0x21
#define SCENE_GREAT_BAY_TEMPLE 0x49
#define SCENE_STONE_TOWER_TEMPLE 0x16
#define SCENE_STONE_TOWER_TEMPLE_INVERTED 0x18
#define UPGRADE_LEVELS 4
// PlayState.aButtonDoAction: a word cell of the action sheet, or none (docs/hud.md).
#define DO_ACTION_NONE 10
#define DO_ACTION_WORDS 38
#define BUTTON_ENABLED 0
#define BUTTON_DISABLED 0xFF

// A node of a layout's tree (docs/hud.md).
#define UI_WIDGET_VISIBLE 0x1 // flags
#define UI_WIDGET_VISIBLE_CHANGED 0x20000 // flags: set by a change; activeFlags: set while visible
#define UI_WIDGET_TRANSLATE_X 0x100 // flags: translate.x was set; activeFlags: it is the default, 0
#define UI_WIDGET_TRANSLATE_Y 0x200
#define UI_WIDGET_SCALE_X 0x800 // flags: scale.x was set; activeFlags: it is the default, 1
#define UI_WIDGET_SCALE_Y 0x1000
#define UI_WIDGET_FLAGS_HIDDEN 0x0FFFFF0E
#define UI_WIDGET_ACTIVE_FLAGS_HIDDEN 0x0FFDFF00

typedef struct UiWidget {
    /* 0x000 */ void* vtable;
    /* 0x004 */ struct UiLayout* owner;
    /* 0x008 */ struct UiWidget** siblings; // the parent's children, NULL for a root
    /* 0x00C */ int32_t index; // in siblings, -1 for a root
    /* 0x010 */ const char* name;
    /* 0x014 */ struct UiWidget** children;
    /* 0x018 */ uint32_t childCount;
    /* 0x01C */ char unk_01C[0x4];
    /* 0x020 */ struct UiLayout* layout; // the layout a widget stands for, or NULL
    /* 0x024 */ char unk_024[0x18];
    /* 0x03C */ Vec3f translate; // from the parent's origin, y down; a root's from the screen's top left
    /* 0x048 */ Vec3f scale;
    /* 0x054 */ char unk_054[0x2C];
    /* 0x080 */ float alpha;
    /* 0x084 */ uint32_t flags; // UI_WIDGET_*
    /* 0x088 */ uint32_t activeFlags;
    /* 0x08C */ char unk_08C[0x54];
    /* 0x0E0 */ float world[3][4]; // the widget's screen transform as last drawn; x moves at [0][3]
    /* 0x110 */ char unk_110[0x2C];
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
    /* 0x190 */ uint16_t textNum; // the label shown: PlayState.aButtonDoAction once the change has played
    /* 0x192 */ uint8_t changeState; // 0 settled, 1 the old word leaving, 2 the new one arriving
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
    /* 0x1B0 */ char unk_1B0[0x54];
    /* 0x204 */ UiWidget* lastTimerGroup; // last_timer_g: the final hours' countdown
    /* 0x208 */ UiWidget* gameTimerGroup; // game_timer_g: the clock, its day bar and frame
    /* 0x20C */ char unk_20C[0x24];
    /* 0x230 */ float opacity; // set every frame; PlayHud_Draw draws nothing at 0
} PlayHud; // size = 0x234 (at least)

// The main touch screen (gUiScreens[UI_SCREEN_MAIN], docs/hud.md "The view icon").
typedef struct MainScreen {
    /* 0x00 */ char unk_00[0x20];
    /* 0x20 */ UiWidget* camChange; // cam_change: the eye, "View"
    /* 0x24 */ UiWidget* camPicture; // cam_picture: the pictograph box
    /* 0x28 */ UiWidget* camReturn; // cam_return: the camera, "Return"
} MainScreen; // size = 0x2C (at least)

// gUiCommonLayouts.
#define UI_LAYOUT_TOUCH_PANEL 0 // Joker.Main.Play.TouchPanel: the main touch screen's HUD
#define UI_LAYOUT_BACKGROUND 1
#define UI_LAYOUT_HUD 2 // PlayHud
#define UI_LAYOUT_COUNT 49

// The frame's 2D draw queues (docs/hud.md "Minimap"): a drawable and its priority per entry, the
// queue drawn in ascending priority.
#define LAYOUT_DRAW_QUEUE_COUNT 8
#define LAYOUT_DRAW_QUEUE_CAPACITY 0x180
#define LAYOUT_DRAW_QUEUE_TOP 4 // the top screen's 2D, over the 3D
#define LAYOUT_DRAW_QUEUE_TOUCH 6 // the touch screen's map
// Graph_DrawTopScreen draws queues 0 to 3 on the top screen, 0 under the 3D and 1 to 3 over it;
// Graph_DrawFrame draws 4 and 5, where the title's, file select's and MainScreen's layouts land on
// the touch screen (docs/ui.md "Title and file select").
#define LAYOUT_DRAW_QUEUE_TOP_BACK 0
#define LAYOUT_DRAW_QUEUE_TOP_1 1
#define LAYOUT_DRAW_QUEUE_TOP_2 2
#define LAYOUT_DRAW_QUEUE_TOP_3 3
#define LAYOUT_DRAW_QUEUE_TOUCH_BACK 4
#define LAYOUT_DRAW_QUEUE_TOUCH_5 5
// Graph_DrawTopScreen's draw of queue 1, from its start.
#define GRAPH_DRAW_TOP_QUEUE_1_CALL 0x2CC

typedef struct LayoutDrawManager {
    /* 0x0000 */ char unk_0000[0x14];
    /* 0x0014 */ uint32_t queueCounts[LAYOUT_DRAW_QUEUE_COUNT];
    /* 0x0034 */ char unk_0034[0x544];
    /* 0x0578 */ void* queues[LAYOUT_DRAW_QUEUE_COUNT][LAYOUT_DRAW_QUEUE_CAPACITY];
    /* 0x3578 */ uint32_t priorities[LAYOUT_DRAW_QUEUE_COUNT][LAYOUT_DRAW_QUEUE_CAPACITY];
} LayoutDrawManager; // size = 0x6578 (at least)

// Screen-space quads made each frame: quad i is the corners scaled by sizes[i], turned by
// rotations[i] and moved to positions[i], in its screen's pixels from the top left.
typedef struct QuadBatch {
    /* 0x000 */ char unk_000[0x2B8];
    /* 0x2B8 */ Vec3f* positions;
    /* 0x2BC */ float* rotations; // 12 a quad: three rows of four
    /* 0x2C0 */ Vec3f* sizes;
    /* 0x2C4 */ uint32_t capacity;
    /* 0x2C8 */ uint32_t count;
    /* 0x2CC */ Vec3f corners[4];
    /* 0x2FC */ char unk_2FC[0x9C];
    /* 0x398 */ float* colors; // 16 a quad: four RGBA corners, or none
} QuadBatch; // size = 0x39C (at least)

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
#define GYRO_READER_DRIFT_RADIUS 0x85C // float: samples this near the newest are averaged with it; negative, none is
#define GYRO_READER_SCALE 0x888 // double[3]: the HID sample times this, rounded, is the reader's raw unit
#define GYRO_READER_DRIFT_BIAS 0x8A0 // float[3], raw units

// The player's look in first person and with an aimed item (Player_UpdateLook).
#define PLAYER_STATE_FLAGS_1 0x11DB0 // u32
#define PLAYER_STATE1_FIRST_PERSON 0x100000
#define PLAYER_STATE1_ITEM_AIMED 0x8 // an item is aimed (the bow); clear in the plain look
#define PLAYER_VIEW_MODE 0x11DF1 // u8, PLAYER_VIEW_* (docs/hud.md "The view icon")
#define PLAYER_VIEW_NONE 0
#define PLAYER_VIEW_FIRST_PERSON 1
#define PLAYER_LOOK_BASE 0x125B8 // s16[3]: focus.rot at the last motion reset
#define PLAYER_LOOK_FLAGS 0x129BC // u32, PLAYER_LOOK_*
#define PLAYER_LOOK_GYRO 0x1 // the gyroscope sets focus.rot; stays set after the look ends
#define PLAYER_LOOK_FIRST_PERSON 0x2 // the player's draw sets it each frame the view is first person
#define PLAYER_PAD 0x129CC // pointer to the pad state the player reads

// Pictograph_IsOn's word: 1 while the pictograph box's view is up.
extern int16_t gPictographOn; // 0x0068D302
extern MotionState gMotionState; // 0x006B1DF4
extern UiLayout* gUiCommonLayouts[UI_LAYOUT_COUNT]; // 0x006B7B8C
extern LayoutDrawManager gLayoutDrawManager; // 0x0071B000
// The touch screen's map in play: the room's two layers, and its markers (the player's arrow).
extern QuadBatch* gMinimapQuads[2]; // 0x006890EC
extern QuadBatch* gMinimapMarkerQuads; // 0x00728198
extern uint8_t sItemIconFrames[ITEM_ICON_COUNT]; // 0x006562F0
extern uint8_t gUpgradeShifts[UPGRADE_COUNT]; // 0x00626C34
extern uint8_t gItemSlots[]; // 0x00626CDC
extern uint32_t gUpgradeMasks[UPGRADE_COUNT]; // 0x00626D3C
extern uint16_t gUpgradeCapacities[UPGRADE_COUNT][UPGRADE_LEVELS]; // 0x00626D60
extern CommonData gCommonData; // 0x007751D8
extern PlayState* gPlayState; // 0x00667890
extern UiScreenContext gUiScreenContext; // 0x0072F5BC
extern void* gUiScreens[UI_SCREEN_COUNT]; // 0x00656B00
// The touch screens of the title (PRESS START) and of file select, outside gUiScreens: activeScreen
// points at one of them outside play (docs/ui.md).
extern TitleScreen gTitleUiScreen; // 0x006F7FB4
extern FileSelectScreen gFileSelectUiScreen; // 0x006F79D4
extern OptionsScreen gOptionsUiScreen; // 0x006F7348
// Where the GPU driver writes its next PICA command (a value, then its header) and the end of the
// list it writes into; the game's own register writes (0x146C00, the GL state flush at 0x10BB00) go
// there too (docs/ui.md "Clipping a layout").
extern uint32_t* gPicaCommandNext; // 0x006A3A88
extern uint32_t* gPicaCommandEnd; // 0x006A3A8C
// The game's stylus read (Input_ReadTouch): it calls nn::hid::TouchPanelReader::ReadLatest at
// INPUT_READ_TOUCH_CALL into a TouchPanelStatus and keeps it in its input at +0x14.
typedef struct TouchPanelStatus {
    /* 0x0 */ uint16_t x; // the touch screen's pixel, 0 to 319
    /* 0x2 */ uint16_t y;
    /* 0x4 */ uint8_t touched;
} TouchPanelStatus; // size = 0x8
#define INPUT_READ_TOUCH_CALL 0x14
// Pad buttons ORed into the next pad update's held word, then cleared (docs/ocarina.md).
extern uint32_t gPadInjected; // 0x0072A0DC
// The touch item buttons as the pad update leaves them: held, and pressed this frame.
extern uint8_t gTouchButtonsHeld; // 0x0072A0ED
extern uint8_t gTouchButtonsPressed; // 0x0072A0EE
extern void* gMessageObject; // 0x006B3724
extern uint8_t gOcarinaSongButtons[][OCARINA_SONG_BUTTONS_SIZE]; // 0x006A2AF6
extern uint8_t gOcarinaListSongs[OCARINA_LIST_SONGS]; // 0x00620D64

#endif
