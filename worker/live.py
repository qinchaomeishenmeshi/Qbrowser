import requests

cookies = {
    "passport_csrf_token": "6dfe5079fe7380eee24a19dc16efca5e",
    "s_v_web_id": "verify_mbkr7l1g_zR2XuZiF_ZKGl_4PP3_A2Tx_f0FNLb0GRTVS",
    "csrf_session_id": "707410702d6372a64d0886b6a9eaea5a",
    "be-token": "",
    "be-token-scene": "",
    "bd_ticket_guard_client_web_domain": "2",
    "__security_mc_1_s_sdk_crypt_sdk": "ef93271f-4d53-9631",
    "__security_mc_1_s_sdk_cert_key": "f7f7a556-49ef-be99",
    "__security_server_data_status": "1",
    "n_mh": "9-mIeuD4wZnlYrrOvfzG3MuT6aQmCUtmr8FxV8Kl8xY",
    "_bd_ticket_crypt_doamin": "3",
    "bd_ticket_guard_client_data": "eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQk1UMW85dzF0Q0dRVUhONlNJM0JLUnAzbFFJdiszODRxT2IwdWJvbHhNZmJEd2lSMlhKajh5ZCtCWEV5QVFxbUtkb2xiaW1GMzVValJCNDdWeG1zMU09IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoxfQ%3D%3D",
    "biz_trace_id": "ce162d44",
    "passport_mfa_token": "Cje8LJdwNGHNAYrPbDItOq%2FF1hi374S2hqr0880kd34Aq2e44atZ3Wnn1lmMhnd%2B6F3IX39Ryks7GkoKPAAAAAAAAAAAAABPGgTrBL0Dtj52RRVMI1cD1AMO7YLYghosbohQUyRNUNE46Wlh1kaiRN9M4Lk2gNigbRDn5vMNGPax0WwgAiIBA50ybwo%3D",
    "d_ticket": "1afb6399de3ce2649905e7ed603af9f664bc8",
    "odin_tt": "ec70dd502d688f3c9b84a3d0da7bab020cc80718cc2e2dff07515514d5dfecec449de2698205589d2b2fb8cd758757e0a97264930f75c9c6dbf5dd8c63ebad8b",
    "passport_assist_user": "CkGV3Gt0aEr_41OZ3LfyEKuIy8nZ1-hClVKBGXcrUVC3O_oqW3gHaZjLqhyJ6XyZsBq_RfgZYocuKz8aXdh8EVpyKBpKCjwAAAAAAAAAAAAATxqZ_B43mBJMrzpKNFTXpkHZOH-Tf-9ZZS-SUBnduq1fis0Vxhjay71zD_Z1pcTMCNgQwefzDRiJr9ZUIAEiAQPXSpNC",
    "sid_guard": "4a2f39ad62cd220698f9d522feaacc7c%7C1749623832%7C5184000%7CSun%2C+10-Aug-2025+06%3A37%3A12+GMT",
    "uid_tt": "9823fbc94bf3196328d3a9b58855ffe2",
    "uid_tt_ss": "9823fbc94bf3196328d3a9b58855ffe2",
    "sid_tt": "4a2f39ad62cd220698f9d522feaacc7c",
    "sessionid": "4a2f39ad62cd220698f9d522feaacc7c",
    "sessionid_ss": "4a2f39ad62cd220698f9d522feaacc7c",
    "is_staff_user": "false",
    "sid_ucp_v1": "1.0.0-KGRmODM0Zjg4MGExNTllNmRmMDQ5NTUxMjA0MmY3YjY4NWU1NDMyYzkKIgj4i8C4tazgBBCYyKTCBhjlnxMgDDC54tXBBjgHQPQHSAQaAmhsIiA0YTJmMzlhZDYyY2QyMjA2OThmOWQ1MjJmZWFhY2M3Yw",
    "ssid_ucp_v1": "1.0.0-KGRmODM0Zjg4MGExNTllNmRmMDQ5NTUxMjA0MmY3YjY4NWU1NDMyYzkKIgj4i8C4tazgBBCYyKTCBhjlnxMgDDC54tXBBjgHQPQHSAQaAmhsIiA0YTJmMzlhZDYyY2QyMjA2OThmOWQ1MjJmZWFhY2M3Yw",
    "bd_ticket_guard_server_data": "eyJ0aWNrZXQiOiI0YTJmMzlhZDYyY2QyMjA2OThmOWQ1MjJmZWFhY2M3YyIsInRzX3NpZ24iOiJ0cy4xLmViZThkMWI3NzgyYTgxMDk2NWY2ZjkyNzhlMzQ0ZmRiNWMyOTc3NzMzNzk5NWRhNjBkNzJlYTZhNGNlNGM1ZTNjNGZiZTg3ZDIzMTljZjA1MzE4NjI0Y2VkYTE0OTExY2E0MDZkZWRiZWJlZGRiMmUzMGZjZThkNGZhMDI1NzVkIiwiY2xpZW50X2NlcnQiOiJwdWIuQkJNVDFvOXcxdENHUVVITjZTSTNCS1JwM2xRSXYrMzg0cU9iMHVib2x4TWZiRHdpUjJYSmo4eWQrQlhFeUFRcW1LZG9sYmltRjM1VWpSQjQ3VnhtczFNPSIsImxvZ19pZCI6IjIwMjUwNjExMTQzNzExMDdCRkJFMTE0RUQ3Q0M4MzUxRUMiLCJjcmVhdGVfdGltZSI6MTc0OTYyMzgzMn0%3D",
    "bd_ticket_guard_web_domain": "3",
    "_bd_ticket_crypt_cookie": "29ec8b58d59df397563867b6496c4251",
    "__security_mc_1_s_sdk_sign_data_key_web_protect": "8878f9fb-4d72-9dc6",
    "gfkadpd": "315365,22350",
    "ttwid": "1%7CaeA_yv5t_veKYz2ffdE_fd61HqHpTpX-iZs6bfpELqk%7C1750648023%7C8d3f3953ede7c7e5bccf0495b24fb418863e90904c0263b35ad4e7b36cabdc0b",
    "eos_s_token": "Ckcdp9TgNgyliwOKmw9gQuxQUofGZJ9GXDAlMofjRs3SQn8gd4Ubj6Ym1FEFaU696ZrgoyT6m9JHhZNxwa031/xOEd4wouu0oRpJCjwAAAAAAAAAAAAATyYuArD6wszKkHgPlqq/psAU58i1mV2sHtyNlV6VAEE69vnkOX9W6fZN8THBBiCn1PYQhOz0DRjB4KnnDyIBA4ydXxw",
    "kura_cloud_uid": "cab6b40caad3aae65550184c9b647ac4",
}

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/json",
    "origin": "https://eos.douyin.com",
    "priority": "u=1, i",
    "referer": "https://eos.douyin.com/dp/liveScreen?room_id=7517571915641391883&enter_from=eos_live_history_page",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "x-secsdk-csrf-token": "0001000000017d2370ba3ad6da291877ed5628ffdec096c074f1d23b65fd68e120b1d0087e8b184b8d270af7a492",
    "x-tt-ls-session-id": "deb4822a-4c54-4970-86fd-6a6a6a9ea1c8",
    "x-tt-trace-id": "00-9ac1c5781882d6ff251e491cb-9ac1c5781882d6ff-01",
    "x-tt-trace-log": "01",
    # 'cookie': 'passport_csrf_token=6dfe5079fe7380eee24a19dc16efca5e; s_v_web_id=verify_mbkr7l1g_zR2XuZiF_ZKGl_4PP3_A2Tx_f0FNLb0GRTVS; csrf_session_id=707410702d6372a64d0886b6a9eaea5a; be-token=; be-token-scene=; bd_ticket_guard_client_web_domain=2; __security_mc_1_s_sdk_crypt_sdk=ef93271f-4d53-9631; __security_mc_1_s_sdk_cert_key=f7f7a556-49ef-be99; __security_server_data_status=1; n_mh=9-mIeuD4wZnlYrrOvfzG3MuT6aQmCUtmr8FxV8Kl8xY; _bd_ticket_crypt_doamin=3; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQk1UMW85dzF0Q0dRVUhONlNJM0JLUnAzbFFJdiszODRxT2IwdWJvbHhNZmJEd2lSMlhKajh5ZCtCWEV5QVFxbUtkb2xiaW1GMzVValJCNDdWeG1zMU09IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoxfQ%3D%3D; biz_trace_id=ce162d44; passport_mfa_token=Cje8LJdwNGHNAYrPbDItOq%2FF1hi374S2hqr0880kd34Aq2e44atZ3Wnn1lmMhnd%2B6F3IX39Ryks7GkoKPAAAAAAAAAAAAABPGgTrBL0Dtj52RRVMI1cD1AMO7YLYghosbohQUyRNUNE46Wlh1kaiRN9M4Lk2gNigbRDn5vMNGPax0WwgAiIBA50ybwo%3D; d_ticket=1afb6399de3ce2649905e7ed603af9f664bc8; odin_tt=ec70dd502d688f3c9b84a3d0da7bab020cc80718cc2e2dff07515514d5dfecec449de2698205589d2b2fb8cd758757e0a97264930f75c9c6dbf5dd8c63ebad8b; passport_assist_user=CkGV3Gt0aEr_41OZ3LfyEKuIy8nZ1-hClVKBGXcrUVC3O_oqW3gHaZjLqhyJ6XyZsBq_RfgZYocuKz8aXdh8EVpyKBpKCjwAAAAAAAAAAAAATxqZ_B43mBJMrzpKNFTXpkHZOH-Tf-9ZZS-SUBnduq1fis0Vxhjay71zD_Z1pcTMCNgQwefzDRiJr9ZUIAEiAQPXSpNC; sid_guard=4a2f39ad62cd220698f9d522feaacc7c%7C1749623832%7C5184000%7CSun%2C+10-Aug-2025+06%3A37%3A12+GMT; uid_tt=9823fbc94bf3196328d3a9b58855ffe2; uid_tt_ss=9823fbc94bf3196328d3a9b58855ffe2; sid_tt=4a2f39ad62cd220698f9d522feaacc7c; sessionid=4a2f39ad62cd220698f9d522feaacc7c; sessionid_ss=4a2f39ad62cd220698f9d522feaacc7c; is_staff_user=false; sid_ucp_v1=1.0.0-KGRmODM0Zjg4MGExNTllNmRmMDQ5NTUxMjA0MmY3YjY4NWU1NDMyYzkKIgj4i8C4tazgBBCYyKTCBhjlnxMgDDC54tXBBjgHQPQHSAQaAmhsIiA0YTJmMzlhZDYyY2QyMjA2OThmOWQ1MjJmZWFhY2M3Yw; ssid_ucp_v1=1.0.0-KGRmODM0Zjg4MGExNTllNmRmMDQ5NTUxMjA0MmY3YjY4NWU1NDMyYzkKIgj4i8C4tazgBBCYyKTCBhjlnxMgDDC54tXBBjgHQPQHSAQaAmhsIiA0YTJmMzlhZDYyY2QyMjA2OThmOWQ1MjJmZWFhY2M3Yw; bd_ticket_guard_server_data=eyJ0aWNrZXQiOiI0YTJmMzlhZDYyY2QyMjA2OThmOWQ1MjJmZWFhY2M3YyIsInRzX3NpZ24iOiJ0cy4xLmViZThkMWI3NzgyYTgxMDk2NWY2ZjkyNzhlMzQ0ZmRiNWMyOTc3NzMzNzk5NWRhNjBkNzJlYTZhNGNlNGM1ZTNjNGZiZTg3ZDIzMTljZjA1MzE4NjI0Y2VkYTE0OTExY2E0MDZkZWRiZWJlZGRiMmUzMGZjZThkNGZhMDI1NzVkIiwiY2xpZW50X2NlcnQiOiJwdWIuQkJNVDFvOXcxdENHUVVITjZTSTNCS1JwM2xRSXYrMzg0cU9iMHVib2x4TWZiRHdpUjJYSmo4eWQrQlhFeUFRcW1LZG9sYmltRjM1VWpSQjQ3VnhtczFNPSIsImxvZ19pZCI6IjIwMjUwNjExMTQzNzExMDdCRkJFMTE0RUQ3Q0M4MzUxRUMiLCJjcmVhdGVfdGltZSI6MTc0OTYyMzgzMn0%3D; bd_ticket_guard_web_domain=3; _bd_ticket_crypt_cookie=29ec8b58d59df397563867b6496c4251; __security_mc_1_s_sdk_sign_data_key_web_protect=8878f9fb-4d72-9dc6; gfkadpd=315365,22350; ttwid=1%7CaeA_yv5t_veKYz2ffdE_fd61HqHpTpX-iZs6bfpELqk%7C1750648023%7C8d3f3953ede7c7e5bccf0495b24fb418863e90904c0263b35ad4e7b36cabdc0b; eos_s_token=Ckcdp9TgNgyliwOKmw9gQuxQUofGZJ9GXDAlMofjRs3SQn8gd4Ubj6Ym1FEFaU696ZrgoyT6m9JHhZNxwa031/xOEd4wouu0oRpJCjwAAAAAAAAAAAAATyYuArD6wszKkHgPlqq/psAU58i1mV2sHtyNlV6VAEE69vnkOX9W6fZN8THBBiCn1PYQhOz0DRjB4KnnDyIBA4ydXxw; kura_cloud_uid=cab6b40caad3aae65550184c9b647ac4',
}

json_data = {
    "room_id": "7517571915641391883",
}

response = requests.post(
    "https://eos.douyin.com/life/api/live_screen/v4/key_index",
    cookies=cookies,
    headers=headers,
    json=json_data,
)

# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
# data = '{"room_id":"7517571915641391883"}'
# response = requests.post('https://eos.douyin.com/life/api/live_screen/v4/key_index', cookies=cookies, headers=headers, data=data)
