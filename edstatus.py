from dataclasses import dataclass
from enum import IntFlag


class EDStatusFlags(IntFlag):
    LANDING_GEAR_DOWN = 4
    IN_SUPERCRUISE = 16
    FLIGHT_ASSIST_OFF = 32
    HARDPOINTS_DEPLOYED = 64
    LIGHTS_ON = 256
    CARGO_SCOOP_DEPLOYED = 512
    SILENT_RUNNING = 1024
    SRV_HANDBRAKE_ON = 4096
    FSD_MASS_LOCKED = 65536
    FSD_CHARGING = 131072
    FSD_COOLDOWN = 262144
    OVERHEATING = 1048576
    HUD_ANALYSIS_MODE = 134217728
    NIGHT_VISON = 268435456
    FSD_JUMP = 1073741824


@dataclass(frozen=True)
class EDStatus:
    landing_gear_down: bool
    in_supercruise: bool
    flight_assist_off: bool
    hard_points_deployed: bool
    lights_on: bool
    cargo_scop_deployed: bool
    silent_running: bool
    srv_handbrake_on: bool
    fsd_mass_locked: bool
    fsd_charging: bool
    fsd_on_cooldown: bool
    overheating: bool
    hud_analysis_mode: bool
    night_vision_on: bool
    fsd_jump: bool

    @classmethod
    def from_int(cls, flags: int) -> EDStatus:
        return cls.from_flags(EDStatusFlags(flags))

    @classmethod
    def from_flags(cls, flags: EDStatusFlags) -> EDStatus:
        return cls(
            landing_gear_down=EDStatusFlags.LANDING_GEAR_DOWN in flags,
            in_supercruise=EDStatusFlags.IN_SUPERCRUISE in flags,
            flight_assist_off=EDStatusFlags.FLIGHT_ASSIST_OFF in flags,
            hard_points_deployed=EDStatusFlags.HARDPOINTS_DEPLOYED in flags,
            lights_on=EDStatusFlags.LIGHTS_ON in flags,
            cargo_scop_deployed=EDStatusFlags.CARGO_SCOOP_DEPLOYED in flags,
            silent_running=EDStatusFlags.SILENT_RUNNING in flags,
            srv_handbrake_on=EDStatusFlags.SRV_HANDBRAKE_ON in flags,
            fsd_mass_locked=EDStatusFlags.FSD_MASS_LOCKED in flags,
            fsd_charging=EDStatusFlags.FSD_CHARGING in flags,
            fsd_on_cooldown=EDStatusFlags.FSD_COOLDOWN in flags,
            overheating=EDStatusFlags.OVERHEATING in flags,
            hud_analysis_mode=EDStatusFlags.HUD_ANALYSIS_MODE in flags,
            night_vision_on=EDStatusFlags.NIGHT_VISON in flags,
            fsd_jump=EDStatusFlags.FSD_JUMP in flags
        )
