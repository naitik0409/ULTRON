from enum import Enum


class IntentType(str, Enum):
    EXIT = "exit"
    GENERAL = "general"
    REALTIME = "realtime"
    CODING = "coding"
    OPEN_APP = "open"
    CLOSE_APP = "close"
    PLAY_MEDIA = "play"
    GENERATE_IMAGE = "generate image"
    SYSTEM_CONTROL = "system"
    SYSTEM_STATUS = "system_status"
    TASK_MANAGE = "task"
    PC_OPTIMIZE = "pc_optimize"
    FILE_OPERATION = "file_operation"
    AUTOMATION = "automation"
    SCHEDULE = "schedule"
    UNKNOWN = "unknown"


ALL_INTENTS = [t.value for t in IntentType]


def map_cohere_to_intent(cohere_decisions: list[str]) -> list[tuple[IntentType, str]]:
    mapped = []
    for decision in cohere_decisions:
        decision = decision.strip().lower()
        matched = False
        for intent in IntentType:
            if decision.startswith(intent.value):
                remaining = decision[len(intent.value):].strip().lstrip("( )").strip()
                mapped.append((intent, remaining))
                matched = True
                break
        if not matched:
            mapped.append((IntentType.UNKNOWN, decision))
    return mapped


def prioritize_intents(mapped: list[tuple[IntentType, str]]) -> list[tuple[IntentType, str]]:
    priority = {
        IntentType.EXIT: 0,
        IntentType.SYSTEM_CONTROL: 1,
        IntentType.OPEN_APP: 1,
        IntentType.CLOSE_APP: 1,
        IntentType.PLAY_MEDIA: 1,
        IntentType.PC_OPTIMIZE: 1,
        IntentType.TASK_MANAGE: 1,
        IntentType.SYSTEM_STATUS: 1,
        IntentType.GENERATE_IMAGE: 2,
        IntentType.REALTIME: 3,
        IntentType.CODING: 4,
        IntentType.SCHEDULE: 5,
        IntentType.FILE_OPERATION: 5,
        IntentType.AUTOMATION: 5,
        IntentType.GENERAL: 6,
        IntentType.UNKNOWN: 7,
    }
    return sorted(mapped, key=lambda x: priority.get(x[0], 99))


def has_coding_intent(mapped: list[tuple[IntentType, str]]) -> bool:
    return any(t == IntentType.CODING for t, _ in mapped)


def has_exit_intent(mapped: list[tuple[IntentType, str]]) -> bool:
    return any(t == IntentType.EXIT for t, _ in mapped)


def has_realtime_intent(mapped: list[tuple[IntentType, str]]) -> bool:
    return any(t == IntentType.REALTIME for t, _ in mapped)


def has_general_intent(mapped: list[tuple[IntentType, str]]) -> bool:
    return any(t == IntentType.GENERAL for t, _ in mapped)


def has_automation_intent(mapped: list[tuple[IntentType, str]]) -> bool:
    automation_types = {
        IntentType.OPEN_APP, IntentType.CLOSE_APP, IntentType.PLAY_MEDIA,
        IntentType.SYSTEM_CONTROL, IntentType.SYSTEM_STATUS, IntentType.TASK_MANAGE,
        IntentType.PC_OPTIMIZE, IntentType.FILE_OPERATION, IntentType.AUTOMATION,
        IntentType.SCHEDULE, IntentType.GENERATE_IMAGE,
    }
    return any(t in automation_types for t, _ in mapped)
