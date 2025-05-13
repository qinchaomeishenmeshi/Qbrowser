import requests

cookies = {
    's_v_web_id': 'verify_ma296x94_cN9qKS1u_Ge77_4GH1_9dKm_CDKfqxgt3h21',
    'passport_csrf_token': 'a0d90f762a253beb2bc71f8d5919cc9e',
    'passport_csrf_token_default': 'a0d90f762a253beb2bc71f8d5919cc9e',
    'is_staff_user': 'false',
    'scmVer': '1.0.1.8918',
    '_tea_utm_cache_3813': 'undefined',
    'ucas_c0': 'CkEKBTEuMC4wELOIh-jlg4KOaBjmJiDa-KC0-s2VBCiwITD9wsDllIyvAUChkPDABkihxKzDBlClvNiW66eL_WZYbhIUO4-MQjRuKaHNQkCP38ut6dsauK0',
    'ucas_c0_ss': 'CkEKBTEuMC4wELOIh-jlg4KOaBjmJiDa-KC0-s2VBCiwITD9wsDllIyvAUChkPDABkihxKzDBlClvNiW66eL_WZYbhIUO4-MQjRuKaHNQkCP38ut6dsauK0',
    'gfkadpd': '2631,22740',
    'ttwid': '1%7CLUSdAxz8HOWvdcfySHjerSV82iglCe6cM3xd6Vh3trI%7C1747015569%7Cac8eb03477316e1e530497cf42d0a248ad3f6d35d7d0b2500d6cf2c48be72926',
    'uid_tt': 'fb19044c03cecb6766a7b4db665b2e0f',
    'uid_tt_ss': 'fb19044c03cecb6766a7b4db665b2e0f',
    'sid_tt': '848c02360d492cdb3a86a07186726279',
    'sessionid': '848c02360d492cdb3a86a07186726279',
    'sessionid_ss': '848c02360d492cdb3a86a07186726279',
    'odin_tt': '59988d2c865d2419e9ec5c6e7cd1d7bed57f0cf004373ce8dc25af8504f537d6c41d6b7b52abaf5cf3c3901397ed3fb6eff6ecbeaba9b19093ddad29562a7abe',
    'ucas_c0_buyin': 'CkEKBTEuMC4wEKeIi4Km8tWQaBi9LyD8lfDOhazIBSiPETD9wsDllIyvAUCVr4XBBkiV48HDBlCovMug0tLbhWhYfhIUza5LZN9yKu9dCUg36_JbUSry8_k',
    'ucas_c0_ss_buyin': 'CkEKBTEuMC4wEKeIi4Km8tWQaBi9LyD8lfDOhazIBSiPETD9wsDllIyvAUCVr4XBBkiV48HDBlCovMug0tLbhWhYfhIUza5LZN9yKu9dCUg36_JbUSry8_k',
    'sid_guard': '848c02360d492cdb3a86a07186726279%7C1747015573%7C5184000%7CFri%2C+11-Jul-2025+02%3A06%3A13+GMT',
    'sid_ucp_v1': '1.0.0-KDc1ODA0ZmI5MDkyY2QxMjZmMmM0ZjEzZWE0MmE1MzMwMTgwNDk5OTQKGAj9wsDllIyvARCVr4XBBhiPESAMOAhAJhoCaGwiIDg0OGMwMjM2MGQ0OTJjZGIzYTg2YTA3MTg2NzI2Mjc5',
    'ssid_ucp_v1': '1.0.0-KDc1ODA0ZmI5MDkyY2QxMjZmMmM0ZjEzZWE0MmE1MzMwMTgwNDk5OTQKGAj9wsDllIyvARCVr4XBBhiPESAMOAhAJhoCaGwiIDg0OGMwMjM2MGQ0OTJjZGIzYTg2YTA3MTg2NzI2Mjc5',
    'SASID': 'SID2_7503373390021067043',
    'BUYIN_SASID': 'SID2_7503373390021067043',
    'buyin_shop_type': '24',
    'buyin_account_child_type': '1128',
    'buyin_app_id': '1128',
    'buyin_shop_type_v2': '24',
    'buyin_account_child_type_v2': '1128',
    'buyin_app_id_v2': '1128',
    # 'csrf_session_id': '5dea7f80d49469041149e18b89d4abbb',
}

headers = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'priority': 'u=1, i',
    'referer': 'https://buyin.jinritemai.com/dashboard/marketing/coupon-manager?pre_universal_page_params_id=&universal_page_params_id=2f0c5cd9-8dc2-4ca8-b86e-9b0b536f8214',
    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    # 'cookie': 's_v_web_id=verify_ma296x94_cN9qKS1u_Ge77_4GH1_9dKm_CDKfqxgt3h21; passport_csrf_token=a0d90f762a253beb2bc71f8d5919cc9e; passport_csrf_token_default=a0d90f762a253beb2bc71f8d5919cc9e; is_staff_user=false; scmVer=1.0.1.8918; _tea_utm_cache_3813=undefined; ucas_c0=CkEKBTEuMC4wELOIh-jlg4KOaBjmJiDa-KC0-s2VBCiwITD9wsDllIyvAUChkPDABkihxKzDBlClvNiW66eL_WZYbhIUO4-MQjRuKaHNQkCP38ut6dsauK0; ucas_c0_ss=CkEKBTEuMC4wELOIh-jlg4KOaBjmJiDa-KC0-s2VBCiwITD9wsDllIyvAUChkPDABkihxKzDBlClvNiW66eL_WZYbhIUO4-MQjRuKaHNQkCP38ut6dsauK0; gfkadpd=2631,22740; ttwid=1%7CLUSdAxz8HOWvdcfySHjerSV82iglCe6cM3xd6Vh3trI%7C1747015569%7Cac8eb03477316e1e530497cf42d0a248ad3f6d35d7d0b2500d6cf2c48be72926; uid_tt=fb19044c03cecb6766a7b4db665b2e0f; uid_tt_ss=fb19044c03cecb6766a7b4db665b2e0f; sid_tt=848c02360d492cdb3a86a07186726279; sessionid=848c02360d492cdb3a86a07186726279; sessionid_ss=848c02360d492cdb3a86a07186726279; odin_tt=59988d2c865d2419e9ec5c6e7cd1d7bed57f0cf004373ce8dc25af8504f537d6c41d6b7b52abaf5cf3c3901397ed3fb6eff6ecbeaba9b19093ddad29562a7abe; ucas_c0_buyin=CkEKBTEuMC4wEKeIi4Km8tWQaBi9LyD8lfDOhazIBSiPETD9wsDllIyvAUCVr4XBBkiV48HDBlCovMug0tLbhWhYfhIUza5LZN9yKu9dCUg36_JbUSry8_k; ucas_c0_ss_buyin=CkEKBTEuMC4wEKeIi4Km8tWQaBi9LyD8lfDOhazIBSiPETD9wsDllIyvAUCVr4XBBkiV48HDBlCovMug0tLbhWhYfhIUza5LZN9yKu9dCUg36_JbUSry8_k; sid_guard=848c02360d492cdb3a86a07186726279%7C1747015573%7C5184000%7CFri%2C+11-Jul-2025+02%3A06%3A13+GMT; sid_ucp_v1=1.0.0-KDc1ODA0ZmI5MDkyY2QxMjZmMmM0ZjEzZWE0MmE1MzMwMTgwNDk5OTQKGAj9wsDllIyvARCVr4XBBhiPESAMOAhAJhoCaGwiIDg0OGMwMjM2MGQ0OTJjZGIzYTg2YTA3MTg2NzI2Mjc5; ssid_ucp_v1=1.0.0-KDc1ODA0ZmI5MDkyY2QxMjZmMmM0ZjEzZWE0MmE1MzMwMTgwNDk5OTQKGAj9wsDllIyvARCVr4XBBhiPESAMOAhAJhoCaGwiIDg0OGMwMjM2MGQ0OTJjZGIzYTg2YTA3MTg2NzI2Mjc5; SASID=SID2_7503373390021067043; BUYIN_SASID=SID2_7503373390021067043; buyin_shop_type=24; buyin_account_child_type=1128; buyin_app_id=1128; buyin_shop_type_v2=24; buyin_account_child_type_v2=1128; buyin_app_id_v2=1128; csrf_session_id=5dea7f80d49469041149e18b89d4abbb',
}

params = {
    '_bid': 'mcenter_buyin',
    '_': '1747119185500',
    's': '962674',
    'promotion_name_or_id': '',
    'page': '1',
    'size': '10',
    'search_type': '1',
    'need_channel': 'false',
    'msToken': 'XClFOeYbnwfwQiJ9QJGaB8P_hx2Igey4ruBcZZ3XVjOmywqGjw8HKhLGNntvN0lHf-zM1RJC7Y2ApdckYZfo3NU1Jjz9zNVDeVKbFpkk6ym_Md5feytr4tTtOyDlTMzrN3vzVicfeT6sZwscGzvml4zBhN-rRdvBiWZIIC7QIvO67uJ08lU45jv2',
    'a_bogus': 'Dv0jketLY28cC3lt8csLSX9lK92MrTSy3HioWPaTtqF/GqMP5IpbxOGQJxuGU2c6YYBehHp7apTMufxbO9swZCKpFmhDud7bOtVA906Lgqi6GeTmgqgOCwWzzwMF0OJweACUNIhRWsMN2nxAVq5kWQBGy5Fo55jdbHZyDMLyeEWgDAukin3sOHkBE6JqqD==',
    'verifyFp': 'verify_ma296x94_cN9qKS1u_Ge77_4GH1_9dKm_CDKfqxgt3h21',
    'fp': 'verify_ma296x94_cN9qKS1u_Ge77_4GH1_9dKm_CDKfqxgt3h21',
}

response = requests.get(
    'https://buyin.jinritemai.com/api/buyin/marketing/anchor_coupon/promotion_list',
    params=params,
    cookies=cookies,
    headers=headers,
)
print(response.text)
