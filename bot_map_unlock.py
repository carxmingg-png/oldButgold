#!/usr/bin/env python3
import sys
import json
import base64
import gzip
import time
import requests

USER_AGENT = 'UnityPlayer/6000.0.64f1 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)'
PROFILE_URL = 'https://street-prod.carx-online.com/str/v1/client/profiles'
TIMEOUT = 60

REAL_ESTATE_PROPERTIES = [
    "apartment_01", "apartment_51", "apartment_95",
    "apartment_industrial_SP", "apartment_midtown_SP", "apartment_midtown2_SP", "apartment_midtown3_SP",
    "Industrial_apartment_1", "Industrial_apartment_2", "Industrial_apartment_3", "Industrial_apartment_4", "Industrial_apartment_5", "Industrial_apartment_6",
    "Midtown_apartment_1", "Midtown_apartment_2", "Midtown_apartment_3", "Midtown_apartment_4", "Midtown_apartment_5", "Midtown_apartment_6",
    "Midtown_apartment_7", "Midtown_apartment_8", "Midtown_apartment_9", "Midtown_apartment_10", "Midtown_apartment_11", "Midtown_apartment_12",
    "Prigorod_apartment_1", "Prigorod_apartment_2", "Prigorod_apartment_3", "Prigorod_apartment_4", "Prigorod_apartment_5", "Prigorod_apartment_6", "Prigorod_apartment_7",
    "Mountain_apartment_1", "Mountain_apartment_2", "Mountain_apartment_3", "Mountain_apartment_4", "Mountain_apartment_5", "Mountain_apartment_6",
    "Mountain_apartment_7", "Mountain_apartment_8", "Mountain_apartment_9", "Mountain_apartment_11", "Mountain_apartment_13", "Mountain_apartment_14",
    "Mountain_apartment_15", "Mountain_apartment_16", "Mountain_apartment_17", "Mountain_apartment_18", "Mountain_apartment_19",
    "Speedway_apartment_1", "Speedway_apartment_2", "Speedway_apartment_3"
]
EXTRA_LOCATION_KEYS = ["car_market_0", "car_showroom_0", "car_showroom_1", "car_showroom_2"]

def create_slot_data():
    real_estates, real_estate_slots = {}, {}
    for prop in REAL_ESTATE_PROPERTIES:
        slots = [{"unlocked": True, "car_id": "", "is_empty": True} for _ in range(3)]
        real_estates[prop] = {"is_bought": True, "slots": slots}
        for i in range(3):
            real_estate_slots[f"{prop}_slot_{i}"] = {"unlocked": True, "car_id": ""}
    return real_estates, real_estate_slots

def unlock_maps_ultimate(profile):
    if 'game_world_parts' not in profile:
        profile['game_world_parts'] = {}
    for m in ['industrial', 'midtown', 'suburb', 'port', 'mountain', 'sunset']:
        profile['game_world_parts'][m] = {"unlocked": True}
    real_estates, real_estate_slots = create_slot_data()
    if 'real_estates' not in profile:
        profile['real_estates'] = {}
    for prop_id, prop_data in real_estates.items():
        if prop_id not in profile['real_estates']:
            profile['real_estates'][prop_id] = prop_data
        else:
            existing = profile['real_estates'][prop_id]
            existing['is_bought'] = True
            if 'slots' not in existing or len(existing.get('slots', [])) != 3:
                existing['slots'] = prop_data['slots']
            else:
                for slot in existing['slots']:
                    slot['unlocked'] = True
                    if 'car_id' not in slot:
                        slot['car_id'] = ""
    if 'real_estate_slots' not in profile:
        profile['real_estate_slots'] = {}
    for slot_id, slot_data in real_estate_slots.items():
        if slot_id not in profile['real_estate_slots']:
            profile['real_estate_slots'][slot_id] = slot_data
        else:
            profile['real_estate_slots'][slot_id]['unlocked'] = True
            if 'car_id' not in profile['real_estate_slots'][slot_id]:
                profile['real_estate_slots'][slot_id]['car_id'] = ""
    if 'locations' not in profile:
        profile['locations'] = {}
    if 'default' not in profile['locations']:
        profile['locations']['default'] = {}
    if 'location_objects_set' not in profile['locations']['default']:
        profile['locations']['default']['location_objects_set'] = {'keys': []}
    loc_keys = profile['locations']['default']['location_objects_set']['keys']
    for p in REAL_ESTATE_PROPERTIES + EXTRA_LOCATION_KEYS:
        if p not in loc_keys:
            loc_keys.append(p)
    if 'race_generators' not in profile:
        profile['race_generators'] = {}
    ts = int(time.time())
    mountain = profile['race_generators'].setdefault('game_world_mountain_farm_races', {})
    mountain['races_counter'] = {"keys": ["mountain_race_farm_drift_DM001", "mountain_race_farm_sprint_ST001", "mountain_race_farm_free_drift_AO01", "mountain_race_farm_gymkhana_ao04"], "values": [1,2,3,4]}
    mountain['races_set'] = {"keys": ["mountain_race_farm_drift_DM005", "mountain_race_farm_sprint_ST004", "mountain_race_farm_free_drift_AO02", "mountain_race_farm_gymkhana_ao08"], "values": [1,2,3,4]}
    sunset = profile['race_generators'].setdefault('game_world_sunset_farm_races', {})
    sunset['races_counter'] = {"keys": ["speedway_race_farm_free_drift_AO01", "speedway_race_farm_sprint_DM01", "speedway_race_farm_sprint_DM05", "speedway_race_farm_gymkhana_ao01"], "values": [1,2,3,4]}
    sunset['races_set'] = {"keys": ["speedway_race_farm_free_drift_AO02", "speedway_race_farm_sprint_DM02", "speedway_race_simple_drift_DM01", "speedway_race_farm_gymkhana_ao01"], "values": [1,2,3,4]}
    if 'races_ts' not in profile:
        profile['races_ts'] = {"keys": [], "values": []}
    all_keys = []
    for gen in [mountain, sunset]:
        all_keys.extend(gen.get('races_counter', {}).get('keys', []))
        all_keys.extend(gen.get('races_set', {}).get('keys', []))
    for k in all_keys:
        if k not in profile['races_ts']['keys']:
            profile['races_ts']['keys'].append(k)
            profile['races_ts']['values'].append(ts)
    profile['is_tutorial_finished'] = True
    profile['tutorial_step'] = 600
    return profile

def compress_data(profile):
    raw = json.dumps(profile, separators=(',', ':')).encode('utf-8')
    gz = gzip.compress(raw)
    return base64.b64encode(len(raw).to_bytes(4, 'little') + gz).decode('ascii')

def get_profile(token):
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json', 'Authorization': f'Bearer {token}'}
    try:
        r = requests.get(PROFILE_URL, headers=headers, timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()['d']['data']
            compressed = data['compressed_data']
            raw = base64.b64decode(compressed)
            return json.loads(gzip.decompress(raw[4:])), None
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)

def save_profile(token, profile, retries=5):
    for attempt in range(retries):
        try:
            b64 = compress_data(profile)
            headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json', 'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            r = requests.post(PROFILE_URL, json={'compressed_data': b64}, headers=headers, timeout=TIMEOUT)
            if r.status_code == 200:
                return True, None
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return False, "Save failed"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "No token provided"}))
        sys.exit(1)
    raw_token = sys.argv[1].strip()
    token = raw_token[7:].strip() if raw_token.startswith("Bearer ") else raw_token
    profile, err = get_profile(token)
    if not profile:
        print(json.dumps({"success": False, "message": f"Failed to get profile: {err}"}))
        sys.exit(1)
    profile = unlock_maps_ultimate(profile)
    ok, err = save_profile(token, profile)
    if ok:
        res = profile.get('resources', {}) or {}
        silver = res.get('soft', {}).get('amount', 0)
        gold = res.get('hard', {}).get('amount', 0)
        xp = res.get('experience', {}).get('amount', 0)
        maps = profile.get('game_world_parts', {}) or {}
        maps_unlocked = sum(1 for v in maps.values() if isinstance(v, dict) and v.get('unlocked'))
        cars_count = len(profile.get('cars', {}).get('items', {}) or {})
        houses_count = len(profile.get('real_estates', {}) or {})
        stats = {
            "cash": silver,
            "gold": gold,
            "exp": xp,
            "maps_count": maps_unlocked,
            "real_estates_count": houses_count,
            "cars_count": cars_count
        }
        print(json.dumps({"success": True, "message": "✅ Done.", "stats": stats, "profile": profile}))
    else:
        print(json.dumps({"success": False, "message": f"❌ Save failed: {err}"}))

if __name__ == '__main__':
    main()
