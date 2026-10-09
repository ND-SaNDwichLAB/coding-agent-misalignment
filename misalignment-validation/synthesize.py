import pandas as pd

specstory_chat = pd.read_json("validated_misalignments-specstory-chat.json")
swe_chat = pd.read_json("validated_misalignments-swe-chat.json")

specstory_chat.drop(columns=["repository_id_old", "session_id_old"], inplace=True)
specstory_chat_valid = specstory_chat[specstory_chat["label"] == "VALID"].copy()
swe_chat_valid = swe_chat[swe_chat["label"] == "VALID"].copy()

specstory_chat_valid["source"] = "specstory"
swe_chat_valid["source"] = "swe"
misalignment_chat_valid = pd.concat(
    [specstory_chat_valid, swe_chat_valid], ignore_index=True
)
misalignment_chat_valid.drop(
    columns=["label", "invalid_category", "note"], inplace=True
)
misalignment_chat_valid.rename(
    columns={"count_id": "count_id_original", "misalignment-id": "misalignment_id"},
    inplace=True,
)
misalignment_chat_valid.to_json(
    "validated_misalignments-all.json",
    orient="records",
    indent=2,
    force_ascii=False,
)
