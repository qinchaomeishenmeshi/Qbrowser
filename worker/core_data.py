import requests

cookies = {
    # 'passport_csrf_token': 'af22b6b201540196a73bedd1cc1fcad2',
    # 'passport_csrf_token_default': 'af22b6b201540196a73bedd1cc1fcad2',
    # 'is_staff_user': 'false',
    # 's_v_web_id': 'verify_mb7ltvo1_KQymAXDT_9Lye_473q_Ae2U_6ihzGZOIbwq4',
    # 'ttwid': '1%7CUFarMQAn7lahebOQjnHPihNvw8-fgRqHNMu3FVXA2Q4%7C1749002018%7C8ee309fbe291eafebc093b75b2247811ac114a06d8669da32531631d12196d4f',
    # 'uid_tt': '6ea87dbd6f2c948da60b6ae94e38da0b',
    # 'uid_tt_ss': '6ea87dbd6f2c948da60b6ae94e38da0b',
    # 'sid_tt': '2e45908f3725dc664bdf258ea0ec45bd',
    # 'sessionid': '2e45908f3725dc664bdf258ea0ec45bd',
    # 'sessionid_ss': '2e45908f3725dc664bdf258ea0ec45bd',
    # 'odin_tt': 'e7bd0de7ab26640cada4adf76a123e45ffa010e6f2f17a802144d2026e219f4b092300db4d7ec9279044c8d2732a61538b9a1d357b8e9e44832872624783c80f',
    # 'BUYIN_SASID': 'SID2_7511905465619661108',
    # 'ucas_c0_compass': 'CkEKBTEuMC4wEI-IkbKxiOqfaBi9LyDTwfDfgaycAyiPETDj2_DigayABUDG0P7BBkjGhLvEBlCTvLeapbrShWhYfhIUrwwRcWUCgkUroJVaHqxzJ_37Xhs',
    # 'ucas_c0_ss_compass': 'CkEKBTEuMC4wEI-IkbKxiOqfaBi9LyDTwfDfgaycAyiPETDj2_DigayABUDG0P7BBkjGhLvEBlCTvLeapbrShWhYfhIUrwwRcWUCgkUroJVaHqxzJ_37Xhs',
    # 'sid_guard': '2e45908f3725dc664bdf258ea0ec45bd%7C1749002310%7C5184000%7CSun%2C+03-Aug-2025+01%3A58%3A30+GMT',
    # 'sid_ucp_v1': '1.0.0-KDA4NTk1NDY5ZGI4OTNlNTljM2YwZmY5MmNhMTk0N2NiYzVhZGJkZjIKGAjj2_DigayABRDG0P7BBhiPESAMOAhAJhoCbHEiIDJlNDU5MDhmMzcyNWRjNjY0YmRmMjU4ZWEwZWM0NWJk',
    # 'ssid_ucp_v1': '1.0.0-KDA4NTk1NDY5ZGI4OTNlNTljM2YwZmY5MmNhMTk0N2NiYzVhZGJkZjIKGAjj2_DigayABRDG0P7BBhiPESAMOAhAJhoCbHEiIDJlNDU5MDhmMzcyNWRjNjY0YmRmMjU4ZWEwZWM0NWJk',
    'LUOPAN_DT': 'session_7511906314851795238',
    # 'COMPASS_LUOPAN_DT': 'session_7511906314851795238',
    # 'Hm_lvt_b6520b076191ab4b36812da4c90f7a5e': '1749002309,1749038074',
    # 'Hm_lpvt_b6520b076191ab4b36812da4c90f7a5e': '1749038074',
    # 'HMACCOUNT': 'FAEB84376CF5728E',
    # 'csrf_session_id': '707410702d6372a64d0886b6a9eaea5a',
}

headers = {
    # 'accept': 'application/json, text/plain, */*',
    # 'accept-language': 'zh-CN,zh;q=0.9',
    # 'priority': 'u=1, i',
    # 'referer': 'https://compass.jinritemai.com/screen/live/talent?live_room_id=7512002735768865571',
    # 'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    # 'sec-ch-ua-mobile': '?0',
    # 'sec-ch-ua-platform': '"macOS"',
    # 'sec-fetch-dest': 'empty',
    # 'sec-fetch-mode': 'cors',
    # 'sec-fetch-site': 'same-origin',
    # 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
}

params = {
    'room_id': '7512002735768865571',
    'index_selected': 'gpm,pay_ucnt,pay_combo_cnt,watch_pay_ucnt_ratio,product_click_pay_ucnt_ratio,online_user_cnt,live_show_watch_cnt_ratio,avg_watch_duration,watch_interact_ucnt_ratio,follow_anchor_ucnt',
    '_lid': '174900436',
    'verifyFp': 'verify_mb7ltvo1_KQymAXDT_9Lye_473q_Ae2U_6ihzGZOIbwq4',
    'fp': 'verify_mb7ltvo1_KQymAXDT_9Lye_473q_Ae2U_6ihzGZOIbwq4',
    # 'msToken': 'WSC6L9PUa73mgeabPw0KhhLc2-hEIxk8BrvDHCZLchTuA=9A-c1w7FSi0ZNZOG82P4SoFoGiHX3mU_dR7wM_=5-b9rKT6g_soi1VtXt8KeGS4ighSDn0kFZx',
    'a_bogus': 'm6WhQQhvDDfT6f6h5-cLfY3q6AF3YD/-0trEMD2f6VV1xL39HMYE9exoP-0vfOgjxG/ZIeYjy4hbT3ohrQ2y8qwf9W0L/25gsDSkKl12so0j53inCLf/E0iE5hsAtFH8svr4iKi8owICSYyhldAJ5kIlO62-zo0/96W=',
}

response = requests.get(
    'https://compass.jinritemai.com/compass_api/author/live/live_screen/core_data',
    params=params,
    cookies=cookies,
    headers=headers,
)

print(response.json())