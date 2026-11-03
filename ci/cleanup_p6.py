"""Owner-run, preview-first cleanup of exact audited repository targets only."""

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

# Populated from the local audit; no target discovery at deletion time.
AUDIT = json.loads(
    '{\n  "guards": {\n    ".github/workflows/ci.yml": "3f11c9ab58d2f7c8ceb'
    'ca0b153a09ccffae06e314545067ddd6b42f7b8e809f4",\n    ".github/workflo'
    'ws/p5c.yml": "62d81a27185e329a0aca14a10e1a1441f6f91572b3f9e61cbd293e'
    '0bb8f9e576",\n    ".github/workflows/release.yml": "5aa32ef8571532349'
    '0a9375336c245b6dbc1911d480fb4aafc4bc3ba7f8bfb1c",\n    ".gitignore": '
    '"84441157a53577a1426b15e4ea0c1475fa9484b130131057dc61d7e21e0ac424",\n'
    '    ".p4-cache/cyrnava-builds/p4/local-A-6m4ne70o/io.github._74Ceril'
    'lion.CyrNava.flatpak": "856cc0ccd82bca263320e2d692a5b3d316543ae320cd'
    '76d9cd42bf42e54a3170",\n    ".p4-cache/cyrnava-builds/p4/local-A-6m4n'
    'e70o/result.json": "5cbdaac664079eed6c6ec77000015c2fcb7b90f88edc68de'
    '6c57e335766252a5",\n    "BACKUP_RESTORE.md": "0fad8e3783c8b31c3a6d94d'
    '5c72fb76d649e4666bdafe926ebdfbd343bdf11ac",\n    "BLOCKNOTE_COMPATIBI'
    'LITY_REPORT.md": "8021a4c4088126404581b7c700fcf9ba8cec363c44abd5d3e3'
    '245a66ba26de12",\n    "CHANGELOG.md": "53e67f5ff3ebf1c75757dd38e6c94e'
    'ab6d764c2ed9ffb5f527dffc5cf7f1b727",\n    "CYRNAVA_VISUAL_REPORT.md":'
    ' "ae71d5e847ceebbc3fa3bedb99a17e47266be8767302d193b4c2b3b8283d6974",'
    '\n    "F09_M2_REPORT.md": "f8f596d6955ec4427bb2a8abbae209b30999d1edd9'
    'a2eb5df3aeba7b4d77565c",\n    "F09_M3_REPORT.md": "330468a3ee2652c248'
    '5579dd078b75c7a6d52256e891ec8d561c2d171cd0e1ce",\n    "F09_M4_REPORT.'
    'md": "17a8dabd4fbb0c9709c6d67ac53d17a04e5c833b9718ec3d0fb5afe3235a03'
    '65",\n    "FEATURES_FF006_FF018_REPORT.md": "0ffdc45b06e91e725270cefe'
    'db5f2952bbf591c0606ec882f4edd55b32cb4d2a",\n    "FF007_REPORT.md": "2'
    'a328e4d7883d0eb229d645e26dcaa161ac9c211e7cf84c4f2a012f7581e8f1d",\n  '
    '  "LIFECYCLE_REPORT.md": "8f4766aeca1b1bb1ab50c45ae7b6d3669057199e3d'
    'd384350b77d9e112e54fe4",\n    "M1_REPORT.md": "cfcdf02ce627fb9ace2ae2'
    '3ca927fc044d8cf2c9f2e7603e2ffcb0086ce501b2",\n    "M2_REPORT.md": "5e'
    '959957e432332029fe3869e12c96f0647544ba39c23bfe93c171145df83b07",\n   '
    ' "M2_VERIFICATION.md": "4ba49576c21ae21cf443c36894557a1290b8317fcfb0'
    'b2cab454530f6dd6be2d",\n    "M4_REPORT.md": "144fd325c2c94d14b88ba12e'
    '25c92c3f3adb32291ae0e7c7e563b75c6d8de3b4",\n    "M4_VERIFICATION.md":'
    ' "33ee21b8c2891d6cdddb40d014155319df6ac76a0d01cf021c670b1f5cf3c616",'
    '\n    "M5_REPORT.md": "500e30eccd419afcfcb7f1b28f5a7612216d062871860d'
    '69082b8c4c80103976",\n    "M5_VERIFICATION.md": "00adf6f5b6d8486ca96c'
    '28cc83af06ab820cd21e28b1be032aad71bf71cf8980",\n    "M6_REPORT.md": "'
    'f2e0ecb1819dd1c6531492058ba2d4a8be022029260197bf74dfbbcf5e825a00",\n '
    '   "M6_VERIFICATION.md": "78dda04939184081974dbdb2331517c5c057cd71ea'
    '5337b3ea31f20d0c63954e",\n    "P2_M01_REPORT.md": "ee6281489ebb9da46c'
    '4d9eb8ac5dd2d5f84de5e328673f031f92a1bbe097f262",\n    "README.md": "8'
    '8853b97500bc21fa13a5433144e01c9e63240bdac64094f88f4f9feed282f53",\n  '
    '  "REBRANDING_REPORT.md": "b76e3148c8095a4d138b83db0a593c5ab200884fd'
    'ce68315574ac2dc7fdc9f70",\n    "VERIFICATION.md": "0818110214d11683e2'
    '99125eaf07d9cc5aa005ce97852ab2cb12d6684fd1420c",\n    "backend/app/__'
    'init__.py": "91447944015cec709e8aa7655f7e9d64e1e4508e7023a57fe374691'
    '1c0fc6fed",\n    "backend/app/__main__.py": "ddee9f27fec4eecb683552bc'
    'ca7d7937ef14809a13662bb7d8f190a7b3da830c",\n    "backend/app/assets.p'
    'y": "93f84ebefc87c75178ba084e58b5d2a686f558330b1f56ec2d0e0ec3dab9ee5'
    '3",\n    "backend/app/backup.py": "794f8170865e8896546e512376fc008dab'
    'caf8523c8501a59c3a052cf78da93b",\n    "backend/app/database.py": "855'
    '8bc0800a77199d211e1b0a839872f1c4464a31439e7effe5b9faafe3389f7",\n    '
    '"backend/app/desktop_security.py": "bd4e54fcfa7d6d147b17f41b633ae763'
    'a97e8a2c4fb914c37b70e796c4fb0ad5",\n    "backend/app/document_format_'
    'v1.json": "25d45408eff2f09102e1b3d6a9a86e5add1832925f056014e743dce53'
    '229118c",\n    "backend/app/documents.py": "e62fd0c9ec83f17a6459a82b2'
    '78576ad5aed10c2c42cccb5697b103c2eaa5a71",\n    "backend/app/lifecycle'
    '.py": "ab79e0ff39964cc9a84d74c869a0cf489f79ffd98d17c22963788aaec238d'
    '852",\n    "backend/app/main.py": "af3fab5cb345fdffc4e3b1e4be5edf0847'
    '83ecc78a5bdc7b7df2c8ce9f74f266",\n    "backend/app/migration.py": "f8'
    '4dbca8829880a777e53e8195b762596950a17411340c8d93c2cfe14707952e",\n   '
    ' "backend/app/migration_benchmark.py": "adce5605ab51056b0d6b8df85e3d'
    '32d1ad70546e783bed50046fc1caf15ed052",\n    "backend/app/migration_cl'
    'i.py": "f8b8d3e6f7f6baf23f84ef8c8f584c8fad6e210dc0a21f6e7c7d3a279d75'
    '9d98",\n    "backend/app/models.py": "41baf13ad2a732263ae22af62cfd65a'
    'c8920e8b72d7e8d6e8138a442a7e7f33a",\n    "backend/app/profile.py": "f'
    'feae924a07053bc9ba3dc8e84cafbc431e496794d576f1ef5917e4d7ecd6844",\n  '
    '  "backend/app/release.py": "af62fd6280b5bca58ff80bff7d3d515104bc45f'
    '15b352a252578709bb925cb2b",\n    "backend/app/search.py": "7e8929e51e'
    '0a1f4513c400214ce0942f3394ec81e6acb8b910199122fa79d781",\n    "backen'
    'd/app/search_index.py": "b145c4dee26d4b1ececbe3f2d51d167b1a160f777c4'
    'b86f2db1b4871fc5d9363",\n    "backend/app/templates.py": "4454bbed154'
    '12f620a6f5da66f873770f12a850d758264ffce7fe367dfa32a07",\n    "backend'
    '/benchmarks/search.py": "cc6ba2522bf5d5798a8722a0bee1c42cd65823323fe'
    'c04d1a3161de30526fd01",\n    "backend/pyproject.toml": "516377e611451'
    '9926d19eeaba32425c70d5493c2eec94b20501478b6319d1e32",\n    "backend/t'
    'ests/conftest.py": "9d8df79235bb79813d85111163d8739a711a7ff539bf6d8a'
    '258d9889b049ba15",\n    "backend/tests/fixtures/blocknote_v1.json": "'
    '523b7685e4e9651f2bfe44ef07590f2450ba35beb562d77e973f576703c6908b",\n '
    '   "backend/tests/search_helpers.py": "5c0306c0c3906ceef8429614e0d30'
    '70ca2e9f0f397bacafb54642ae057374a7a",\n    "backend/tests/test_assets'
    '.py": "443420d6debfea54e67eba3406dec9de95e45102e1d5ca917c73b79e734b9'
    'eb3",\n    "backend/tests/test_backup.py": "2a844ed7c503ca64254500048'
    '162cd55a0d6d2629c2faa580164bf2d65657a28",\n    "backend/tests/test_de'
    'sktop.py": "bdc94c843cbf5d30ec02c94d021c3494a53c28a322790740a469cafb'
    'c2de02ae",\n    "backend/tests/test_desktop_security.py": "4dcec80ed9'
    'a33c63eeec0568e7b7e7fed72a4368f1c09ad527b0f32d42e16d4e",\n    "backen'
    'd/tests/test_document_compatibility.py": "6bb97ad8fe180993e75f57ddb2'
    '014a26b0990daca08a30f860541c4f6ba6920a",\n    "backend/tests/test_fla'
    'tpak_candidate.py": "740ee3bb7ce3a719a65e58637f6dde2694e8380a1dc2351'
    'b5af4a6bf6d2226ad",\n    "backend/tests/test_health.py": "5b194f64df9'
    'e7a559e649e255c1ada55b0ea2b86e331333d8b610bbaa9a089b3",\n    "backend'
    '/tests/test_library.py": "21db8a4d0425bbe3c526e716ae6d7a711351cec296'
    'f57cd462194cf3686a8d10",\n    "backend/tests/test_lifecycle.py": "ff4'
    'a417bd099a0d07d693edcb657819313549c288ca60b3cb35a57401185fe05",\n    '
    '"backend/tests/test_lifecycle_harness.py": "55f7de2f1e356bfcc64d3247'
    'e098f0859e7c152ac72a7d70a28e890ce2ec7e8a",\n    "backend/tests/test_m'
    'igration.py": "7897d0c544b0800a6e01c8b7e3f31811f1b84c5b523a089f7077e'
    '82e18245ca0",\n    "backend/tests/test_native_desktop.py": "212c397bd'
    '941703cf2b2f3c16bd7df0e436f5473958a8666d7692044aadbbc3a",\n    "backe'
    'nd/tests/test_native_dialogs.py": "38270464f21e32c9481f282da9f02d23b'
    'f243ae64253edef359243ec351a43a4",\n    "backend/tests/test_native_nav'
    'igation.py": "b0721e14f9ada889aed3859c77932483973abe260a4b37bd48c2a4'
    '0b5e60c3e7",\n    "backend/tests/test_notes.py": "800e28953cbe1158cdf'
    '14377579ed35bb004c6c000ebbcddd39c02f1bb337929",\n    "backend/tests/t'
    'est_rebranding_migration.py": "2c87d7af8340eecde0b7f1b1fa73a3cb77825'
    '1e3f8b9de66e162590ed671c47d",\n    "backend/tests/test_release.py": "'
    '84e3e772eb190e633173b4011021df7f5cacda591afd0c0213f8dbc31aca3f41",\n '
    '   "backend/tests/test_reliability.py": "421e217b84f9265ca0f158b23f3'
    '0d35fae189fe4cbc902785de8baa4c2a89848",\n    "backend/tests/test_sear'
    'ch.py": "3e80766a0e13b520bf45a387677eb3c4fbd2a4969c017622612c1ee7f13'
    '536cf",\n    "backend/tests/test_search_benchmark.py": "1797f4f28b4e1'
    '8856161f2c9fde132d069417f8cfdbe334dd16c094966ad447e",\n    "backend/t'
    'ests/test_search_index.py": "fcebafd8a80837395e37ea1668d777d4ef35afc'
    '9dd379a56f16509ded0fe4d1c",\n    "backend/tests/test_templates.py": "'
    '81d9466a259165ef90dc951f05ba8035286444d3830ce23cc684a08684246187",\n '
    '   "ci/P5A_IMAGE_SELECTION_CORRECTION.md": "21579619f075cdec8008b4d8'
    '7a1f69543fcd90496063e6afb432d3751c47ed0b",\n    "ci/P5A_LIFECYCLE_INV'
    'ESTIGATION.md": "5fa8a028035f387c84588413484c58e0389a3c2cef0acf3dfdd'
    '4cac47caf5eec",\n    "ci/P5A_OWNER_CHECKS.md": "382cdfa93288515caec7c'
    'd4f00b0c74248cd22543acae64461c5efe29e69e9f3",\n    "ci/P5A_PROVISIONI'
    'NG_CORRECTION.md": "0d60d77295573a5528398d5b82f6c58c53a01badab910d6b'
    'f418e688f606979c",\n    "ci/P5A_REPORT.md": "83758c9219dd705706cc27c5'
    'e1f3e077ca20236113e6d90e5bf731e5076db906",\n    "ci/P5B_APPEARANCE_CO'
    'RRECTION.md": "7ed5b4e16fb0b8c8c6a98ebd4cbdc36474be88559212430842b82'
    'ca88a33c73e",\n    "ci/P5B_CLOSEOUT_REVIEW.md": "cb442750f668d418af1d'
    '2cec36e5d267858ca06826fba5f51ac509860c00d6bd",\n    "ci/P5B_GITHUB_ST'
    'AGING_PLAN.md": "42ea5ffb342f1a23f66cd22009926905f50d1d89ecc16660767'
    'd0d58a8d81c05",\n    "ci/P5B_HOSTING_DECISION.md": "b6cc3c778273b8295'
    '541f8a9814636b060d7e95ce8a7f84267e4841b283926ef",\n    "ci/P5B_OWNER_'
    'CHECKS.md": "91ef144117d940a8cbf6a45e54e367605ab7213e1b74d993d2d35d6'
    '2d8d18834",\n    "ci/P5B_REPORT.md": "3c37172a4578f0313f00ee3be9d2846'
    '59afe1c38c70d746ec0df797761ea18fb",\n    "ci/P5B_SIGNING_DESIGN.md": '
    '"14589b9ec6e94bb56b27fb1dbe69c0a43ade36362d77e5928956b38311c689dc",\n'
    '    "ci/P5C_CLOSEOUT_PROPOSAL.md": "d2495a4035ef4e80e1a3905111250887'
    'daaf7b2281a3604fdf15da4be22f4e1f",\n    "ci/P5C_OWNER_CHECKS.md": "fa'
    '6315f48fbffca24682f1efe29e5d0f137c3e237eae3b99a0212298bdeb39fc",\n   '
    ' "ci/P5C_PLAN.md": "f8daa72e5dbfc1478a0c7a82663d16d0830fb3774fd27eda'
    'ed3e6aea2f4c0bd7",\n    "ci/P5C_REPORT.md": "e26c4bedc4493351120624ec'
    '36a10660bb63c79fe215bf5193d2a43897095fdd",\n    "ci/P6_LICENSE_REVIEW'
    '.md": "184e9419b3489f3e7730dcce5e802f01ee9dde6d90c24793a6968b686cc7b'
    'cf3",\n    "ci/P6_OWNER_CHECKS.md": "a9512560b94d58ac640207db69ffcefc'
    '68b7165b54db7c33d36a5a8861f1d8c6",\n    "ci/P6_PLAN.md": "4de055b4908'
    '974d5d08611e9383c3e79bb3ae80d7e12e3f3b74616b4f0e34f0a",\n    "ci/P6_Q'
    'T_COMPATIBILITY.md": "de11e946dd90e759e5be14836ecafc8f9a95813055ef02'
    '330cf0e8925cce1d41",\n    "ci/P6_RELEASE_RUNBOOK.md": "40ddc07f4f5aa4'
    '04623e9fffa58539d5727c5e2adc603ded7e5352115a8fd338",\n    "ci/P6_REPO'
    'RT.md": "44c72e6b3bbd21ee1d7c76052f8abc400358277350e76db276a1b0e88b7'
    '2c8aa",\n    "ci/P6_RUNTIME_REMEDIATION.md": "3261e8ce8a5bf189d8f934e'
    '1761907fa11d4e94dd52949a27216a82191ee751d",\n    "ci/P6_TARGETED_B_CH'
    'ECKS.md": "072538a4e1d445166e8d4c9d7e0fd502068d0dd0b5ac9444f4eeb05e9'
    '663af12",\n    "ci/README.md": "c09098e5d81bd4995d236a5965c9fdd269845'
    'cfbb1545b7e4991c7c5694ce17a",\n    "ci/bootstrap.py": "6945f3bf05928d'
    '4ed616205c5a941d210ecec2f1e04137f8e3001d10051a6438",\n    "ci/evidenc'
    'e/p6/binary-route-2026-11-02/P4-extracted-payload-proof.json": "8254'
    'e0454c60392dd8d2c33f10253375de5458ca692c90ddb656b98b4b25e5a4",\n    "'
    'ci/evidence/p6/binary-route-2026-11-02/artifact-preservation.json": '
    '"77774ecf6bda74b0c5745f2dae455e37f601928d74448892231e0d4b9d920159",\n'
    '    "ci/evidence/p6/binary-route-2026-11-02/binary-evaluation.json":'
    ' "599cb39e5de020a2598bbce84344fb5666586f281f04bb39c0c9a71aa0857c5f",'
    '\n    "ci/evidence/p6/binary-route-2026-11-02/cache-reaudit.json": "3'
    '0afdd452be7878fad3aad0431b9774118bb9cbf39fa39ae5e1b3032b18d18d7",\n  '
    '  "ci/evidence/p6/binary-route-2026-11-02/environment.json": "cbb187'
    'a2318fa1e6fd367f4586d89f38a438af5a5cbaeb0e7561dfa4d7c06a4c",\n    "ci'
    '/evidence/p6/binary-route-2026-11-02/phase-reconciliation.json": "b9'
    '4b9786b8ae9a21955c12d03389f33b17fe47c3ce7500ef34b81cf0606dcd18",\n   '
    ' "ci/evidence/p6/binary-route-2026-11-02/preservation.json": "8a718c'
    '75531e124b875c35c53cab17d694344f2867501a956ebcd26b3a93b3f3",\n    "ci'
    '/evidence/p6/binary-route-2026-11-02/resource-budget.json": "1ba6531'
    '11d04d072b57ec7d7e2a9d6a9146ef2291fcc66169d32a193a8a1cf2e",\n    "ci/'
    'evidence/p6/binary-route-2026-11-02/verification.json": "0f8429a6555'
    '544ec89ef7fe15d1b20960f62e0ab833b58eefba4de74fc375462",\n    "ci/evid'
    'ence/p6/binary-route-2026-11-02/working-source-identity.json": "587d'
    'bd2202767cf0bf8538aad6c2486cb42ff4e491d499311be909817963a1bb",\n    "'
    'ci/flatpak.py": "74168678c6c3446a601f76bbec735dcfaed4f3b5ebeef5d3092'
    'c54d88464cb0f",\n    "ci/lifecycle_harness.py": "f5045d6b8395435ed6db'
    '4ed79f954fa298cceceea40c8caecc5b3d0cf3d086bd",\n    "ci/release/audit'
    '_candidate.py": "061d3b80ddf313c9dcfecd1a4077c84ac3f29662de2004c8cec'
    '5d3f5fc521490",\n    "ci/release/client.py": "a1060610b8d6d54a69ba8f7'
    '8cf4716baf6723d7379655cfacd97a6a79380d4be",\n    "ci/release/core.py"'
    ': "02e759307a20514c77b01fda817b776a14b40722981fa666e2dacbc3451f6fde"'
    ',\n    "ci/release/distribution.py": "391a01d03643f3f305e0d99c9794de5'
    '54e696c1efb68750ff8fce000a23a2ad3",\n    "ci/release/github.py": "466'
    'ebcdf38e3fa404a628131a9804449f62faedb4ad0d52b029025e532453efc",\n    '
    '"ci/release/historical_runtime.py": "37163c752ca707a885d60973ea61312'
    '9a5c815183b2310c469f65f7072ab2ba1",\n    "ci/release/integration.py":'
    ' "8378c53e964d7df2636a192d2750ee4c5fa619a77d1a72233a4c2b7a49bee285",'
    '\n    "ci/release/integration_policy.py": "944cf4eee9dabefd82f351b6cb'
    '17f3895632946a2a432ab31d588104738ba9bf",\n    "ci/release/key_ceremon'
    'y.py": "86810d3e17e318185a332785ac5381111ad3f7c5f270668ba995c4c76737'
    '3dd1",\n    "ci/release/native_diagnostics.py": "bd3da8e5bc0d2c7ec7bc'
    '5605f1ae2c82771423af63f3c482809279f355639b70",\n    "ci/release/nativ'
    'e_distribution.py": "1cc5769a74b3b17f4e59f074c9ffd33f3a177a5d18ddc9c'
    '911ef2ee82392c87c",\n    "ci/release/p5c-workflow-contract.json": "b0'
    '3bbdd59ed3cfaaebbd1036013dff1deaa4f54dec47ac26bceee84c4bb0d452",\n   '
    ' "ci/release/p5c-workflow.yml": "62d81a27185e329a0aca14a10e1a1441f6f'
    '91572b3f9e61cbd293e0bb8f9e576",\n    "ci/release/plan.py": "f7e672e3a'
    '77efbb883a413570e782356c2fa4d0a73f9a5f51fb39592562f5202",\n    "ci/re'
    'lease/policy.json": "d66a7f3c4de34d259349f2e28f47b53ed240170b6643650'
    'b673e29aa7e2a43f4",\n    "ci/release/preference_contract.py": "45b656'
    '7b16ccd26b48d69c4908d6b176ec71045539c698e958e3caeab9d08941",\n    "ci'
    '/release/preflight.py": "290de0f9081a1704cab03a6d1e7dab02385b3a29c14'
    'd2472b1d95e87a6f14bef",\n    "ci/release/product_inventory.py": "630d'
    '1aa7117d37de6ff4b9a2055cbdba100ae8d4773695415a1bba27777bf0ad",\n    "'
    'ci/release/progress.py": "b93f6761f27c9359f3984b71a0e3af190acf7d9e9a'
    'e97cdd01e90b83e597dab5",\n    "ci/release/readiness.py": "fd0d2f7c015'
    '7e45a1e160af574ba0f2d0697dc589f8f4928a8af7444359b3bca",\n    "ci/rele'
    'ase/real_update.py": "30d41c8e259ca0f4d1e036a9edbe0d6f5f1830c4993851'
    'ae092b3261cffbee5b",\n    "ci/release/real_update_audit.py": "7b907ea'
    '52634bdb02b2b57b702a42dac1f2787774cbafe6dabe6ce80f738fbd5",\n    "ci/'
    'release/recovery.py": "87c030904d71c921b5d1942de236d7cc6fe565b64017d'
    '2529b3aa797218c567c",\n    "ci/release/registration-only.yml": "3a8c4'
    'ad86f958dc7d437c5ee4e5ad2ac57d8753cc4429252edc0005bf385c7c5",\n    "c'
    'i/release/registration_policy.py": "8af292b7989f7796a93e64cc13fb9891'
    '5422b287f3c1f73aa7aa03ccde18b32f",\n    "ci/release/stage.py": "ea05f'
    '4833be8cf77adcb5270c6ad2445aa4dfcf2a977ea3d5dc830ad753944ba",\n    "c'
    'i/release/targeted-b-policy.json": "9c94df420932f96d39286ca46a5ad47d'
    '15ed43b6712bfe4795c58f7714412e43",\n    "ci/release/targeted_b.py": "'
    '37c8797f5107d9b2331f6c19aad97004633a368651a9b3dd835c080d62aa2d4e",\n '
    '   "ci/release/targeted_workspace.py": "ae5f68dcbe96df26e382c1529f2a'
    'fe004824a9e3ad48f4405c23399c5c75df23",\n    "ci/release/test_dependen'
    'cies.py": "16d57c728fe942a8de62b1acda8808881b3c6f509d36c0d9b986c7f6d'
    'f372f03",\n    "ci/release/test_distribution.py": "9fc439a7c46625caa6'
    'f7e32a48819343abd061b869913b2eefc6fb2b8aee34c4",\n    "ci/release/tes'
    't_historical_install.py": "d7e437ba17e19957826593f6b0466f5819223180d'
    '84732c06629c2d18ce07915",\n    "ci/release/test_historical_runtime.py'
    '": "8117c35a93c05d9c76307ae91a68a5f971a837aa1bfe09137a7a39e031c516b1'
    '",\n    "ci/release/test_integration.py": "8dc96fac9ac92409897a406891'
    '3fe6319a358a74b58143802cabcbab24d660d3",\n    "ci/release/test_native'
    '_diagnostics.py": "8553bf04e346192861aa2e8e974a750fb150b77d73996593f'
    'c7d080ee1db8244",\n    "ci/release/test_native_phase_context.py": "49'
    '0bc8352f0ecaeab363308e3d42dbaa95063c79ade244f3e4171c918db4c56f",\n   '
    ' "ci/release/test_policy.py": "cba293d0709aea98bd5d99fc40b008270b2b2'
    'f8d00d72bc55fc3d31d6899b661",\n    "ci/release/test_preference_contra'
    'ct.py": "6afdf6238051b3294878264c287312bfd6eb3c7cd78b9f342728478f834'
    'b8392",\n    "ci/release/test_progress.py": "335a32eb7f458c697690cabb'
    '57ff1991dcc4869a32b3ddeef9fb7d780e5613a7",\n    "ci/release/test_real'
    '_update_audit.py": "57e652809b5556c4532cfde51f95b5bae4e3319aa0d10b3e'
    '39a11a178da85787",\n    "ci/release/test_registration.py": "f14382887'
    'e51c0bff00e9da54dd1cc25c8b28a465429b97062ec11b2697897cc",\n    "ci/re'
    'lease/test_runtime_identity.py": "7850f80f400d1bc30dfb8caf36a671f1f1'
    '0cf6d573fe4da3e6a756b7fb35ac50",\n    "ci/release/test_signing.py": "'
    '3f01576d068c43d007b09c08faaa3e64693ca8c7e73d46369bbe81c68412387a",\n '
    '   "ci/release/test_source_checkout.py": "19abbcd1d7aafa6046c6247d0c'
    'a6207eb4c6c35aa35c3f23213344dfc9d836b5",\n    "ci/release/test_target'
    'ed_b.py": "3b324f97eb4e11cda30a978bcacddf80fb0c09bfbbc38434519be7f3b'
    '6309551",\n    "ci/release/trust.py": "5b302aa94c1295f5cb5f5f96258589'
    '0e43b33d936c8667881548d4f47f3d371c",\n    "ci/release/update_fixture.'
    'py": "eb3d2384746129f9a6757783857be3baee5c3fde32de04f40017148d908868'
    'aa",\n    "ci/release/workflow-contract.json": "c47e12e61786633ebf342'
    '778dab85644944b6c11e8c74b9ce00dfe85ace45100",\n    "ci/release/workfl'
    'ow_policy.py": "43b2e3412c08c203175ba2ead95c62faa8f862daf2fdf474ae5b'
    '4b33f662a4a6",\n    "ci/requirements.lock": "2322c771f1efab20a6dfd3ec'
    '414de1c5ad934099aae347ceef167fdb4dd5de73",\n    "ci/test_ci.py": "6ef'
    '6dd80821aeb5309eb87571cd51d09f2cb50510f4e63999c799e96c9391c0c",\n    '
    '"ci/test_cleanup_p6.py": "f5067191a3108fde4fa9780f659259102c77a9160d'
    '4b8391b0182416559cdbe6",\n    "ci/tools.json": "c13a0a5f9374fa95b722f'
    'ce61869f5c121ea01d3f51776e91c86ef1137436c2c",\n    "ci/validate.py": '
    '"9371632e6c4c2f3b9a09ce67f8f7c4e04605f34c5b73df292bc84b87cf80bf2b",\n'
    '    "ci/verify.py": "5b97848f13e3d2be9ebcffc295ee1d60994e59794903d1c'
    'd0fa3ba4f06161b36",\n    "cleanup_cyrnava.sh": "9775ddb52e9ecc2fb78b6'
    '689e1e0ecb7829d48dc6913fae18350cec33840bf62",\n    "desktop/generate_'
    'icons.py": "6b497758b9e6dc37e83688ad4dd3720731eff280e773fc311659bd12'
    '011f7108",\n    "desktop/icons/README.md": "a147a73fc991ab78bb2ba28d9'
    'a6ece3764751a1afe3eedc0bacb3c37ef7e5a90",\n    "desktop/install.py": '
    '"4b94041a8b19104e42128d58a022f6de36a1a63023e0e8d22394a2368fff0eca",\n'
    '    "desktop/launcher.py": "331b33b24899a678e5e81160e1359fd9b7188d6b'
    '29ac6089ae4eb999978494b7",\n    "desktop/native/P2_REPORT.md": "daa8a'
    'c9305df7103f84c593724059d59300d87b555fb429c5bc96686620b459d",\n    "d'
    'esktop/native/P3_NATIVE_CHECKS.md": "69aab5e699bc388a8d8473c9c94bb1d'
    '0fb13e8c491cf57128b9cdd9fefc9c93c",\n    "desktop/native/P3_REPORT.md'
    '": "26737f04678c222c3ed4e81fbc4d76c4df04ea78cbc46dc2e9f58368208d0f03'
    '",\n    "desktop/native/P4_REPORT.md": "1ff86c4350a53f67c3b0a5447315a'
    '203e0b1516c7285ce3fef525d7369abd289",\n    "desktop/native/__init__.p'
    'y": "5d8e2fc0f1f1c3c25222a4a412d3b8599c6f2aba29365959d76d3afe537e5f0'
    '4",\n    "desktop/native/__main__.py": "7e6d5c72c20e4f8155a33642c1738'
    'a6afc539634fabd282827563dd243f0d240",\n    "desktop/native/applicatio'
    'n.py": "bbcc38bf1974a8696a8fe1664bae3551f275eae7a71a7194d434d2d3e982'
    'f3ad",\n    "desktop/native/backend.py": "f29f9f7f37e3cbc8c809542284e'
    '3c464d30212fdd0f4612698ad65b7b87996ea",\n    "desktop/native/build_id'
    'entity.py": "b8f3fa22d49486bc678d7614c839e932599be5197a5deffb10e6ec4'
    '65591a918",\n    "desktop/native/dialogs.py": "d73a0622f5f481124ef644'
    '6b233827cb98d32d3695524523482ef9f5df2ee033",\n    "desktop/native/evi'
    'dence/p4/package-inventory.json": "daf4f3d6ae60974e3095af908fa82cb25'
    'bdbdd20326046426dd28a4c9f4a3a8a",\n    "desktop/native/identity.py": '
    '"40f473e91380e55c159ec14f1f166801191f3fde72101b270ee821d02d4d7c70",\n'
    '    "desktop/native/maintenance.py": "d8e1ff7f0a64b56654da1307382dd0'
    '225ab985552ede1fa7f35a7466a1c07a03",\n    "desktop/native/maintenance'
    '_io.py": "a161405d57e7abe71b4ca5a0bf32f862a1bbf5cdd93d3b79a2102a481e'
    'a1c36c",\n    "desktop/native/policy.py": "3cc1614c65721b9b024a168162'
    '13d26b75982c059c565babf41bf51b3ba5bb25",\n    "desktop/native/storage'
    '.py": "e70874a0f764fe1ce684b9975bffa2bd4dbd01f010e7d16e2748388a96f70'
    '030",\n    "desktop/native/worker.py": "7c6b558209b02683d74c065493bf6'
    'ce663682e0328d6a44fe1fc13e5522170fc",\n    "docs/adr/ADR-001.md": "04'
    '21fd8106d5802b2570d9168ceb8610a175d184c64f51dd8bfdf770f0ecc3a8",\n   '
    ' "docs/adr/ADR-002.md": "447ed03ce2a1f494091f4547833a774cf6f3dec8094'
    'f2e2a5d065ae75b8f4775",\n    "docs/adr/ADR-003.md": "5a6844aceb5bc429'
    'b28ca0870edff1d25ac8480bb63ad63cd400a96aab89e198",\n    "docs/adr/ADR'
    '-004.md": "249f7d6680f51b9c0c4c1ef5baf1e430dc25d952ecfa94c8754807ad7'
    '7bb15fb",\n    "docs/adr/ADR-005.md": "b3368a028543b247e485aa3ef9ac5f'
    'aec02de371232e5e8922d27d2ac47a7226",\n    "docs/adr/README.md": "0ea6'
    'ea4ec28c82f4047bc329f6a33f89db5a10486952fbd5dc8343ad62cb7470",\n    "'
    'docs/architecture.md": "d2c1d74ccfd25f4e92e24ab14db6e211ba726791563d'
    '0479631847ebc5ed853a",\n    "docs/dependencies-and-licenses.md": "e38'
    'faa7e58bdcdb048462792272a377b9ba75f20a517ee7516f6d4c173c484f6",\n    '
    '"docs/dependency-inventory.json": "c71befe67d0fc30f88c2237886dc926da'
    '01219ec00b98f05f2bdd28a457e1943",\n    "docs/desktop-launcher.md": "6'
    '88e0a70d879abf45987b0335468bdc29034ceaa37f1f3a34f8961240a861039",\n  '
    '  "docs/document-format.md": "c72237691444ad08ae14c48e32ebaefa7ebca7'
    '8c55e5b8229d080b57d0ebb468",\n    "docs/migrate-to-cyrnava.md": "924a'
    'd72e07fc5616c922d14324661cd90a0dac356e728cae567ec379cc241559",\n    "'
    'docs/release-audit.md": "5bf5bfc3043b729f4bfa013ae20d3d02101567345ed'
    '7a14ad55a0b26a8d0508e",\n    "docs/release-checklist.md": "a2262f3138'
    'def499658d692ec6e66c86926fbfe656e415d3e257c7141552dc67",\n    "docs/r'
    'elease-notes-v0.1.0.md": "85655388631ba41414d9fbb3190c1a52abb91b957a'
    'c84d0ed3c4500e1ec89537",\n    "docs/search-benchmark-results.json": "'
    'ea4df4bff7cd567cc877b5b7cd6ecbc80cf030e3f1b4745c4a2610c0ca252f05",\n '
    '   "docs/search-benchmark.md": "c6ae42bb1ec8178c084245bd0ff5997cb462'
    'd8a7ff9a16268182a76cb913afd3",\n    "docs/search-release-checklist.md'
    '": "ffda8b316f72d5eb84da625af06aa7812884c6b98c70a05cbbb6d78ba03ffe2b'
    '",\n    "docs/search.md": "0d94010aa6776720f58872758277066a05b1fc3924'
    'bb7997e0c782ed730730aa",\n    "frontend/e2e/editorSelection.ts": "b52'
    '8027e903a6a9c3102e62f342e5ecc86283cae4d14c5bec968250953e10755",\n    '
    '"frontend/e2e/lifecycle.spec.ts": "edcbcb5c52df17590ab79c3dea894574a'
    '49a236472e923302e1a8050a3b1047a",\n    "frontend/e2e/search.spec.ts":'
    ' "41717ddd06739a9dea2ae6317d0b6c9c54661fed1519b48c71a90d068e935839",'
    '\n    "frontend/e2e/workspace.spec.ts": "0d530d1a82c521079cf829b442c6'
    '19ecc405319fd71bb24bb34f74af8a9fa993",\n    "frontend/package-lock.js'
    'on": "15ea009817e106931e02f72be1b72c261e83c9eedff153ba03da10540946e4'
    '21",\n    "frontend/package.json": "699b573a740477b221e586cb0c94106cb'
    'b83daf6e9072a566f272356b3d42d65",\n    "frontend/playwright.config.ts'
    '": "481befcad000efc964a6401f192e38515b12547d4c82e008c50feb7ea36b2548'
    '",\n    "frontend/scripts/check-minimatch.mjs": "6f77813454dafd1700ca'
    '7c6b66de4ebb48f98920e89173030cc8796bcf4effb8",\n    "frontend/scripts'
    '/export-document-contract.mjs": "9f17fe6a56f18f173691663d8c6cff154da'
    '9f1ffdacfb0544416cdceb9e7740f",\n    "frontend/src/App.test.tsx": "f8'
    'f8bd5d5d3df7a2bb1ee119a2dfd33a675caa3afa872466f3b63ba67e574d10",\n   '
    ' "frontend/src/App.tsx": "5ab0f760cc444d9e85bb135a55ac3713dc44b7d312'
    '89f72b7be072e0e73573c7",\n    "frontend/src/appearance.test.tsx": "f2'
    'fa543ade8b66f06b170c854425548affb2613daa44717e4fbb1d476c91f75c",\n   '
    ' "frontend/src/appearance.tsx": "b24b714ad5142f35beebf65fdf2d842e107'
    'd6625ff41d4b97f209c9c82ac216c",\n    "frontend/src/appearanceContext.'
    'ts": "5caa1b4d82c4307595e891971959e0dd2d6a52af63cca063b81434921b2532'
    'da",\n    "frontend/src/assets.test.ts": "185d55cc16ac84f781444a90415'
    '2efc32690548228963c0408a76091be6bea26",\n    "frontend/src/assets.ts"'
    ': "30148e594071df7933ffd41a7a564b64e8fc515cfa63593633a283e769a5cd3b"'
    ',\n    "frontend/src/components/ConflictRecovery.test.tsx": "0c6ee213'
    'c1f6a37dcfd35eaf50294096de78bddc76ebcd4b578a29bf82a0b7d1",\n    "fron'
    'tend/src/components/ConflictRecovery.tsx": "56e90f4785bbed87945853b5'
    '0ca6675ed25b9f2beb76b1f7eabe491b096adc5e",\n    "frontend/src/compone'
    'nts/DirectoryTree.test.tsx": "e1379584637bc592b84eadf50d8f31bcc3bf3e'
    'ac2a76617d714a7b46f8239e4d",\n    "frontend/src/components/DirectoryT'
    'ree.tsx": "fa21af4dad05f864905b9a4e0744fff881d587f57d0b88310e587a0dd'
    '33787a5",\n    "frontend/src/components/DraftRecovery.test.tsx": "43c'
    '8f805f683f31b0c7cda955d40e8b67302040d6e4b3b92cd88e5026548f7dd",\n    '
    '"frontend/src/components/GlobalSearch.test.tsx": "cbb56067b3510d8cfd'
    '9758f90f74797cf97d57c442b4a2fec35c4b7178d850ae",\n    "frontend/src/c'
    'omponents/GlobalSearch.tsx": "31ce943a9f31755c4116159970adc5a815d1d3'
    '83159003a3c5396d47ba677a95",\n    "frontend/src/components/Icon.tsx":'
    ' "67fb13508e3d610924e8e636795fceb592b1cc6a7a4d82c610405c3afdfa6fe2",'
    '\n    "frontend/src/components/KnowledgeEditor.test.tsx": "0fbba33269'
    'a57f09638446f50ba9c4f4e6e2a1f715282c0c8ce4cc0bea276022",\n    "fronte'
    'nd/src/components/KnowledgeEditor.tsx": "6a9d528a532917e103f24cb113e'
    'ca50757a8ce684980044c13afccad79a62899",\n    "frontend/src/components'
    '/ManagementDialog.tsx": "36d985f45655a39acfbc3c5629dc1bb2f35332fda73'
    '058d454e1dec38ed0913a",\n    "frontend/src/components/PersistentNote.'
    'test.tsx": "8e9324c9c39806fa5c84964f9bc42a1fc567a6e729cabc30f47ab868'
    'bb698ed5",\n    "frontend/src/components/PersistentNote.tsx": "0ee99c'
    'e53d8f79f64c93b4a46efdc45479e72357ec05bd8aac6e6d2056ef49f7",\n    "fr'
    'ontend/src/components/TemplateManager.test.tsx": "117d6d2163ff9c7fc5'
    '5a4e9e020cdc92361e26c2ece4f97b402c4cb8e10f7a6f",\n    "frontend/src/c'
    'omponents/TemplateManager.tsx": "9ab64d86e41fa5fc0b3ef12a2ccbba3ea06'
    'c6b2970a0dc23ad2d5282927a05f5",\n    "frontend/src/components/editorC'
    'ompatibility.test.ts": "ce5874f344f795b398dceb40395bc7ba15e53239ff3c'
    'be048f4c9f835b9e15ca",\n    "frontend/src/components/editorDocument.t'
    's": "02bd9d771edf8b4b02329ada43f96c8b63d97dd1a1e12f7e66e308ca5adf76c'
    '1",\n    "frontend/src/components/editorRoundTrip.test.tsx": "43ea8f6'
    '8c6830ad12d338858662a9cdce8feb9a43d4e79bd54c3accea418574f",\n    "fro'
    'ntend/src/components/editorSchema.ts": "f53c0075ee019b7b6ddfda4fc88d'
    '5741bfc290b3bf556d7fb93317d21eb473b4",\n    "frontend/src/cyrnavaThem'
    'e.ts": "db7abddded357b7bf737910366ff159631b34ed81c5c46861aca850c3280'
    '70a7",\n    "frontend/src/drafts.test.ts": "3ca2f2def90863e4057f047ec'
    '33fda403a2f7418078e5f80f1fe1ff0fdc053bc",\n    "frontend/src/drafts.t'
    's": "eae271c31a440252618c2d4591abb5c6bf41873261b6b53765b0873e61295e6'
    '8",\n    "frontend/src/hooks/useAutosave.test.tsx": "db2499fd1a75091f'
    '6a2419ea7951f60a3972afb68ebc13a942af7f6dc8690e39",\n    "frontend/src'
    '/hooks/useAutosave.ts": "9dd00bbb56c3e9fab4288cc1a9acf49e81803084431'
    '78827245a339519e3669f",\n    "frontend/src/hooks/useDesktopClose.test'
    '.tsx": "7dba8c441bc7ef5b3c4e63d7f5513e750e371da685f8ecc9badbccdae60d'
    'afb6",\n    "frontend/src/hooks/useDesktopClose.ts": "008b0bdaad5d454'
    'a0bc9ad16b18f3844f0564c8facb0317c4650040c1aa77dad",\n    "frontend/sr'
    'c/hooks/useLifecycle.test.tsx": "6466dc816acfcc81ed8e41a26d18cd53d70'
    'baf327ab1afe93b306fd89967410d",\n    "frontend/src/hooks/useLifecycle'
    '.ts": "809bd7bedab97b22617425fad0d997ba723645173efeb444876307e716c2e'
    '4e2",\n    "frontend/src/http.ts": "ad4531cd73c0edc25abdcf96183278052'
    'b003e341ea89f1a552facd6f6a94a0a",\n    "frontend/src/library.test.ts"'
    ': "9606f0da4762a90196499cf8a4c9b1fb8c80490d3f0b73d59728616fadcd2976"'
    ',\n    "frontend/src/library.ts": "795eee895b4de96bacbf556392931bf8e2'
    '4fe0cd91b072b2a1d8a3b8957db315",\n    "frontend/src/main.tsx": "083fc'
    '61de5ae6f59dffae7e91422b240505aa8e75f2afb3bfa7bc7a4ae59a7ff",\n    "f'
    'rontend/src/notes.test.ts": "dc063ac2bdb8335870f307fec726aa2fc2b6599'
    'fbb61c62533c515a65a2574ba",\n    "frontend/src/notes.ts": "655e352d36'
    '6faaa4bb2ee7747d94bcd23e936b8ea7395f491fb45935ed43c0ee",\n    "fronte'
    'nd/src/pendingMutations.ts": "f697318fd5bbc16e61c5dbe95be773f5c2ca67'
    '94e0a30c17c918e5492a889406",\n    "frontend/src/search.test.ts": "2bb'
    '2454fda78b0dc7b13c96763ba8f850bdb6ab7cd75d1958cc45f1450d61c89",\n    '
    '"frontend/src/search.ts": "61812ac9118d12d9613d87e568ef6d0e0d6143c92'
    '3157b676c6f90923f0fa634",\n    "frontend/src/templates.test.ts": "38f'
    '396991cec404483710497b986af6ea4786eb7f396ad70a0e35ba5ccc0bc50",\n    '
    '"frontend/src/templates.ts": "b69ef66659b40aad81933f86b01dab0a5a5da6'
    '8f53765adead1b0f1457e90fd9",\n    "frontend/src/test-setup.ts": "4af7'
    '97ffb650de5161454d6361370779ac7fb0c35c252a49dc53458535cef65f",\n    "'
    'frontend/src/tree.test.ts": "d3fb9072548250f69f85ccc701f5b6f2a453d67'
    'c5301baeee006694dca618132",\n    "frontend/src/tree.ts": "c25588ce3ce'
    '401b3e6de4905c6471662958a0197c26c55b1fc7ff09a2cd22b4b",\n    "fronten'
    'd/src/viteConfig.test.ts": "6479c7ee4de703a6c34b33509b738375cb534099'
    '4c2f3bc4a9f18df6a6d4ff70",\n    "frontend/tsconfig.json": "54daec310b'
    'e8b4521077f2d7d66621aab1464ae71aa9aad5ba0a087254fd5852",\n    "fronte'
    'nd/vite.config.ts": "fe434794627a0c391d30540cf3f28989b0b5a4ecfe094da'
    '6a9db1a31c06d84c5",\n    "migrate_to_cyrnava.sh": "d06eb4f00a809e55de'
    'f9d7ee3cee930317081a754449f5f54982f8497d25251b",\n    "packaging/flat'
    'pak/P2_NATIVE_CHECKS.md": "d5a4c7417472d5eeedd933932c1518f63e449d6a6'
    '3411d7cb3d6ff18d7e70e0f",\n    "packaging/flatpak/README.md": "8236eb'
    'e3bcb67e815b3c67e676d46a1b8a9ea56d6842d60d0db91d176b5a5ada",\n    "pa'
    'ckaging/flatpak/compatibility/qt-6.11.3-feasibility/README.md": "e67'
    'a9171bdcaf5e11487eb8188c5ee4767a27844ec564fc749a6077a1aea1217",\n    '
    '"packaging/flatpak/prepare.py": "4d4e3b11048bd70b355a220f4c56650a670'
    '180469c52ac7df98d6e9e9b13c7be",\n    "packaging/flatpak/production/P4'
    '_NATIVE_CHECKS.md": "d3319701468df33d7670b9a0bb72ae3a990031529e59015'
    'adb718b27f14b3546",\n    "packaging/flatpak/production/README.md": "1'
    '998b17772bb502859b1144de3715a4005e1ea05b90fe92cdbeee7b5ee365710",\n  '
    '  "packaging/flatpak/production/build.py": "66f64360e3d18be3fbe2b171'
    '8e17a4da76e88c4ea2475d8fd8f97bdd2f9332f4",\n    "packaging/flatpak/pr'
    'oduction/build_identity.py": "7c4ce5e9f4f89d71b4916cbc4753c9770b945b'
    '1836297f8cd41b564598156974",\n    "packaging/flatpak/production/host_'
    'verify.py": "adc03e27b1e8615df16cc52d707f990291890060ec83c0f0a5d04a6'
    'cc771f7e4",\n    "packaging/flatpak/production/install_payload.py": "'
    'b1fe69f2234fa3c5ef8082df20907741216908bf06fa45b0b365a5763f39bbbc",\n '
    '   "packaging/flatpak/production/io.github._74Cerillion.CyrNava.json'
    '": "b659d34322837ad1639e214c8b8550057bb8fdb0ff4fbb18cbf892eb7bec6bc7'
    '",\n    "packaging/flatpak/production/native_check.py": "d5b675f2638f'
    '514e8c22ce8d70a41842000f0292d37efad9ecf503f37b842169",\n    "packagin'
    'g/flatpak/production/requirements.lock": "f5f0ae7c0576b45dee80b1a97b'
    'd4110064ce29e2a192f6adb027780c14cde742",\n    "packaging/flatpak/prod'
    'uction/test_packaging.py": "cbc74ffcb8e2c0d7c38d95ceb4280f4c7b5c2215'
    '7d3988517292d2c0b9034bc0",\n    "packaging/flatpak/production/test_pr'
    'ofile_diagnostics.py": "01dea2dc8f2de50f5fa018e629e0a96624fbfccb58f2'
    '1361589d8931d977b955",\n    "packaging/flatpak/production/toolchain.l'
    'ock.json": "30ba11e377126073164dc13cc103c9873a405766840e8c3992d698bf'
    '7f18483e",\n    "packaging/flatpak/qt_migration_check.py": "29ba2f688'
    '3909e341eead78af513e317e6f63c5b8c9481080316dddf08902390",\n    "packa'
    'ging/flatpak/qt_migration_portal_check.py": "a70bdb1b62d9f3a08643e5f'
    'f29f552253a238151ee71f63a42eafbfa75ecf6f0",\n    "packaging/flatpak/q'
    't_outage_driver_check.py": "f401ca7f85508c0082023746fe782fc483311ae4'
    '0b92562b3e14e45b8ddba98b",\n    "packaging/flatpak/run_migration_veri'
    'fication.py": "01a1bbdae9dc57e44cd48254bc9b47b12971b874e00a050b8225b'
    '288a5ceddd3",\n    "packaging/flatpak/run_portal_verification.py": "8'
    '51814ae931a7e7a94c1630f8b7c297a141273bb1c93fa61088e1e0e2c6e68ff",\n  '
    '  "packaging/flatpak/test_run_migration_verification.py": "f794271a8'
    '354353be69ee4ce33345ed21e9af06821322443fe6d9eaaa63648f8",\n    "packa'
    'ging/flatpak/test_run_portal_verification.py": "a3f134ccbb69e23f79fc'
    '58b99d9ff6ceec62719b1f17f73e9422c5bf0791002c",\n    "packaging/flatpa'
    'k/test_verify_outage.py": "2fddf17f6040aa6d514c887ef7cc82cf5c3b76e89'
    '40585d76589d4e457f19f13",\n    "packaging/flatpak/verify_migration.py'
    '": "2695e2495ea5f056475bce86483b5ea76cd1bcc074b1c79cb672cec4852dc56b'
    '",\n    "packaging/flatpak/verify_native.py": "a83c41ee3095082012efca'
    '932f888826cf1c87640a28b8c1ec9bb3830baa3a38",\n    "packaging/flatpak/'
    'verify_outage.py": "d4e5025c567074f7dc653b265e3429c2979e6bc5c70f0c9c'
    '6775fab251d8089b",\n    "packaging/flatpak/verify_upload.py": "73c762'
    '245c78f7632fb2e6680682ece922da969b5c09fb91c1698340e23d5b9e"\n  },\n  "'
    'head": "bfa0b8005a3ddc519354fd7907e9b972fde8126b",\n  "index_stage_sh'
    'a256": "87223663fe0905b675555ebe973e33de0ab124c7a3c7296e84ba419f9b14'
    '3cca",\n  "root": "/home/cerillion/Documents/Codex/2026-10-21/role-ac'
    't-as-an-implementation-partner/outputs/CyrNava",\n  "root_identity": '
    '[\n    66309,\n    1708169\n  ],\n  "targets": [\n    {\n      "allocated_'
    'bytes": 365522944,\n      "estimated_reclaim_bytes": 365522944,\n     '
    ' "fingerprint": "28e6a6b88df9ad044187d716980856ccc7df141459af40df098'
    '0881c19471a03",\n      "path": "ci-output/p5b-clean/checkout/frontend'
    '/node_modules",\n      "reason": "Obsolete P5B test checkout dependen'
    'cies; recreate from retained checkout lockfile; current frontend/nod'
    'e_modules kept"\n    },\n    {\n      "allocated_bytes": 365531136,\n   '
    '   "estimated_reclaim_bytes": 365531136,\n      "fingerprint": "7eebc'
    '16e26a8ded3203ec3c31eb91e91b4c95c5e07d876c42b4a109c165e97c7",\n      '
    '"path": "ci-output/p5b-appearance-clean/checkout/frontend/node_modul'
    'es",\n      "reason": "Obsolete appearance-investigation dependencies'
    '; recreate from retained lockfile; all source/Git and evidence kept"'
    '\n    },\n    {\n      "allocated_bytes": 73252864,\n      "estimated_re'
    'claim_bytes": 73252864,\n      "fingerprint": "0ed17a156f916bc49144cc'
    '880c9dc41945dadfee98183bdcc4d19ec31e1f4ac4",\n      "path": "ci-outpu'
    't/p6-npm-cache",\n      "reason": "Regenerable npm HTTP/content cache'
    '; installed working dependencies kept"\n    },\n    {\n      "allocated'
    '_bytes": 29450240,\n      "estimated_reclaim_bytes": 29450240,\n      '
    '"fingerprint": "1ab964430f0dc500bd4afec8ce484b51451c8c47a251b8068858'
    '7edc3388f35b",\n      "path": "ci-output/p6-pip-cache",\n      "reason'
    '": "Regenerable pip download cache; installed Python environments ke'
    'pt"\n    },\n    {\n      "allocated_bytes": 210239488,\n      "estimate'
    'd_reclaim_bytes": 210239488,\n      "fingerprint": "009c8cef525388cc7'
    'c1cc0c2fea57a90f5e99d82e1dc3ebda48a6094292e6830",\n      "path": "ci-'
    'output/p5b-hosted-41205351385/package.zip",\n      "reason": "Superse'
    'ded ordinary-CI bundle output; exact result/build-input/provenance J'
    'SON retained and verified; not approved A/B or current release input'
    '"\n    },\n    {\n      "allocated_bytes": 210247680,\n      "estimated_'
    'reclaim_bytes": 210247680,\n      "fingerprint": "b75459000a0d042a5ab'
    '0dda7cd98bb7f04c79bb9b29460e745d1427d513f2bd6",\n      "path": "ci-ou'
    'tput/p5b-hosted-41207770532/package.zip",\n      "reason": "Supersede'
    'd ordinary-CI bundle output; exact result/build-input/provenance JSO'
    'N retained and verified; not approved A/B or current release input"\n'
    '    },\n    {\n      "allocated_bytes": 210247680,\n      "estimated_re'
    'claim_bytes": 210247680,\n      "fingerprint": "63feb98b03b48b0d5ebdc'
    '4dbd1979caa8e44ee4e5fbe150f2948329a6674a742",\n      "path": "ci-outp'
    'ut/p5b-hosted-ci-41258927530/package.zip",\n      "reason": "Supersed'
    'ed ordinary-CI bundle output; exact result/build-input/provenance JS'
    'ON retained and verified; not approved A/B or current release input"'
    '\n    },\n    {\n      "allocated_bytes": 210239488,\n      "estimated_r'
    'eclaim_bytes": 210239488,\n      "fingerprint": "72532169cd96337891d5'
    '46049c758ae9a1052201cc7287c4c411d156cc5b4c13",\n      "path": "ci-out'
    'put/p5b-hosted-ci-41264318875/package.zip",\n      "reason": "Superse'
    'ded ordinary-CI bundle output; exact result/build-input/provenance J'
    'SON retained and verified; not approved A/B or current release input'
    '"\n    },\n    {\n      "allocated_bytes": 49152,\n      "estimated_recl'
    'aim_bytes": 49152,\n      "fingerprint": "d6fcf273c7dc8e7b2f6b999b9ca'
    '90e39a955ca04a8754fb124262be88fffa5ff",\n      "path": ".pytest_cache'
    '",\n      "reason": "Regenerable test/lint/bytecode cache; source fil'
    'es verified present; no source or environment deletion"\n    },\n    {'
    '\n      "allocated_bytes": 131072,\n      "estimated_reclaim_bytes": 1'
    '31072,\n      "fingerprint": "c77a768d9e12d3c39fcfa2ad92907d6d0760018'
    '8319b72dac0a3a80c98d1b8af",\n      "path": ".ruff_cache",\n      "reas'
    'on": "Regenerable test/lint/bytecode cache; source files verified pr'
    'esent; no source or environment deletion"\n    },\n    {\n      "alloca'
    'ted_bytes": 86016,\n      "estimated_reclaim_bytes": 86016,\n      "fi'
    'ngerprint": "32a50824f4208187fca0c913253c3861f9ce34c2ebf3525f386bdba'
    '76eb1f379",\n      "path": "backend/.pytest_cache",\n      "reason": "'
    'Regenerable test/lint/bytecode cache; source files verified present;'
    ' no source or environment deletion"\n    },\n    {\n      "allocated_by'
    'tes": 53248,\n      "estimated_reclaim_bytes": 53248,\n      "fingerpr'
    'int": "a3d67da23d01fc760bfb3f16a00d605b2957b3c80103ff5d11ffe9cd2f320'
    '775",\n      "path": "backend/.ruff_cache",\n      "reason": "Regenera'
    'ble test/lint/bytecode cache; source files verified present; no sour'
    'ce or environment deletion"\n    },\n    {\n      "allocated_bytes": 51'
    '2000,\n      "estimated_reclaim_bytes": 512000,\n      "fingerprint": '
    '"d36e0b3b7a868e021d25dda24ac38a043d299ba9cb59dd81c0fd9e3c107ca6f8",\n'
    '      "path": "backend/app/__pycache__",\n      "reason": "Regenerabl'
    'e test/lint/bytecode cache; source files verified present; no source'
    ' or environment deletion"\n    },\n    {\n      "allocated_bytes": 9338'
    '88,\n      "estimated_reclaim_bytes": 933888,\n      "fingerprint": "a'
    '02f0b387b2c1e0cb567ac39f992a8d220c9e3260e49ff7fee462c1425845805",\n  '
    '    "path": "backend/tests/__pycache__",\n      "reason": "Regenerabl'
    'e test/lint/bytecode cache; source files verified present; no source'
    ' or environment deletion"\n    },\n    {\n      "allocated_bytes": 3031'
    '04,\n      "estimated_reclaim_bytes": 303104,\n      "fingerprint": "8'
    '3e9ce301458df269bf4cd3d6a63ee124b14f3828e31c956d82f1ed31af3496a",\n  '
    '    "path": "desktop/native/__pycache__",\n      "reason": "Regenerab'
    'le test/lint/bytecode cache; source files verified present; no sourc'
    'e or environment deletion"\n    },\n    {\n      "allocated_bytes": 491'
    '52,\n      "estimated_reclaim_bytes": 49152,\n      "fingerprint": "f1'
    'f0cd73968f3518bfb71355c5a6aad2151df612bee7675471b1139ff87cddfe",\n   '
    '   "path": "desktop/__pycache__",\n      "reason": "Regenerable test/'
    'lint/bytecode cache; source files verified present; no source or env'
    'ironment deletion"\n    },\n    {\n      "allocated_bytes": 200704,\n   '
    '   "estimated_reclaim_bytes": 200704,\n      "fingerprint": "49c2b411'
    '4f09392ec7aff15928e3aeec766757c64dbdaf309412ec76a6144cca",\n      "pa'
    'th": "ci/__pycache__",\n      "reason": "Regenerable test/lint/byteco'
    'de cache; source files verified present; no source or environment de'
    'letion"\n    },\n    {\n      "allocated_bytes": 679936,\n      "estimat'
    'ed_reclaim_bytes": 679936,\n      "fingerprint": "bd76d95ffe52f5a5682'
    'cc5c01e870ce37478f8494e00041bb965357913ca2ebc",\n      "path": "ci/re'
    'lease/__pycache__",\n      "reason": "Regenerable bytecode; four rece'
    'nt cp312 files explicitly verified equal to compilation of current s'
    'ource and timestamp/size headers after guard detected change; later '
    'changes still abort"\n    },\n    {\n      "allocated_bytes": 290816,\n '
    '     "estimated_reclaim_bytes": 290816,\n      "fingerprint": "a47887'
    'f855da4d597258e9cd059cde09ab77d1f158c6c20eb47cd28906c679d9",\n      "'
    'path": "packaging/flatpak/production/__pycache__",\n      "reason": "'
    'Regenerable test/lint/bytecode cache; source files verified present;'
    ' no source or environment deletion"\n    },\n    {\n      "allocated_by'
    'tes": 997265408,\n      "estimated_reclaim_bytes": 997265408,\n      "'
    'fingerprint": "83cbd006b9d0c0cb40bc68ecf434923fed8e104a119435b624417'
    '3c7927a84e8",\n      "path": ".p4-cache/cyrnava-builds/p4/local-A-6m4'
    'ne70o/build/files",\n      "reason": "Regenerable extracted P4 app pa'
    'yload; all 5320 inventory entries match retained acceptance inventor'
    'y; exact bundle/hash and source/staged inputs remain; native checker'
    ' consumes bundle, not this tree; do-not-repeat finish history retire'
    'd"\n    }\n  ]\n}'
)


class Refused(RuntimeError):
    pass


def require(value, message):
    if not value:
        raise Refused(message)


def identity(st):
    return [
        st.st_dev,
        st.st_ino,
        st.st_mode,
        st.st_size,
        st.st_mtime_ns,
        st.st_ctime_ns,
        st.st_nlink,
        st.st_blocks,
    ]


def components(root, relative):
    parts = Path(relative).parts
    require(
        parts
        and not Path(relative).is_absolute()
        and all(p not in ("", ".", "..", ".git") for p in parts),
        "Invalid target",
    )
    p = root
    for part in parts[:-1]:
        p = p / part
        require(stat.S_ISDIR(p.lstat().st_mode), "Changed or symlinked ancestor")
    return parts


def mount_check(root, relative, mount_text=None):
    target = root / relative
    text = (
        Path("/proc/self/mountinfo").read_text() if mount_text is None else mount_text
    )
    for line in text.splitlines():
        fields = line.split()
        require(len(fields) >= 6, "Cannot parse mount inventory")
        name = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), fields[4])
        p = Path(name)
        if p == root:
            continue
        require(
            not (
                p.is_relative_to(root)
                and (p.is_relative_to(target) or target.is_relative_to(p))
            ),
            "Mount intersects audited target",
        )


def snapshot(root, relative):
    """No symlink following; content plus inode/metadata detects changed targets."""
    parts = components(root, relative)
    device = root.stat().st_dev
    entries = {}
    allocated = reclaimable = 0
    seen = set()

    def visit(path, rel):
        nonlocal allocated, reclaimable
        st = path.lstat()
        require(st.st_dev == device, "Unexpected filesystem")
        row = {"stat": identity(st)}
        if stat.S_ISLNK(st.st_mode):
            row["link"] = os.readlink(path)
            require(path.resolve(strict=False).is_relative_to(root), "Symlink escape")
        elif stat.S_ISDIR(st.st_mode):
            row["children"] = sorted(os.listdir(path))
        elif stat.S_ISREG(st.st_mode):
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                require(identity(os.fstat(fd)) == row["stat"], "Changed file")
                with os.fdopen(fd, "rb", closefd=False) as stream:
                    row["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
                require(
                    identity(os.fstat(fd)) == row["stat"], "File changed while hashing"
                )
            finally:
                os.close(fd)
        else:
            raise Refused("Unexpected special filesystem object")
        key = (st.st_dev, st.st_ino)
        if key not in seen:
            allocated += st.st_blocks * 512
            if stat.S_ISDIR(st.st_mode) or st.st_nlink == 1:
                reclaimable += st.st_blocks * 512
            seen.add(key)
        entries[rel] = row
        for name in row.get("children", []):
            visit(path / name, rel + "/" + name)

    visit(root.joinpath(*parts), relative)
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    return {
        "fingerprint": hashlib.sha256(encoded).hexdigest(),
        "allocated_bytes": allocated,
        "estimated_reclaim_bytes": reclaimable,
        "entries": entries,
    }


def editor_service(comm, argv):
    """Recognize specific editor services, never arbitrary interpreter activity.

    This exempts only the repository-cwd heuristic. Target handles, executables,
    mappings and cwd are still checked. Unknown workers remain fail-closed.
    """
    if not argv:
        return False
    names = {Path(arg).name for arg in argv[1:] if not arg.startswith("-")}
    if comm == "node":
        return bool(
            names
            & {
                "tsserver.js",
                "typingsInstaller.js",
                "eslintServer.js",
                "pyright-langserver",
                "pyright-langserver.js",
                "typescript-language-server",
                "vscode-json-language-server",
                "vscode-css-language-server",
                "vscode-html-language-server",
            }
        )
    if comm.startswith("python"):
        return bool(names & {"pylsp", "pylsp.__main__", "jedi-language-server"})
    return False


def assert_idle(root, targets):
    """Refuse relevant same-owner activity or open handles into any target."""
    own = os.getpid()
    ancestors = {own}
    current = own
    while current > 1:
        try:
            status = Path(f"/proc/{current}/status").read_text()
            current = int(re.search(r"^PPid:\s+(\d+)", status, re.MULTILINE)[1])
            ancestors.add(current)
        except (OSError, TypeError):
            break
    absolute = [str(root / t["path"]) for t in targets]

    def inside(value):
        value = value.removesuffix(" (deleted)")
        return any(value == p or value.startswith(p + "/") for p in absolute)

    relevant = {
        "node",
        "npm",
        "npx",
        "pytest",
        "ruff",
        "flatpak",
        "flatpak-builder",
        "ninja",
        "cmake",
        "make",
        "gcc",
        "g++",
        "clang",
        "clang++",
        "uvicorn",
    }
    for item in Path("/proc").iterdir():
        if not item.name.isdigit() or int(item.name) in ancestors:
            continue
        try:
            if item.stat().st_uid != os.getuid():
                continue
            comm = (item / "comm").read_text().strip()
            try:
                cwd = os.readlink(item / "cwd")
            except PermissionError:
                require(
                    not (comm in relevant or comm.startswith("python")),
                    f"Cannot inspect relevant process {item.name}; stop it first",
                )
                continue
            require(not inside(cwd), f"Target in use by process {item.name}")
            is_tool = comm in relevant or comm.startswith("python")
            if is_tool and (cwd == str(root) or cwd.startswith(str(root) + "/")):
                argv = (
                    (item / "cmdline")
                    .read_bytes()
                    .decode("utf-8", errors="replace")
                    .rstrip("\0")
                    .split("\0")
                )
                require(
                    editor_service(comm, argv),
                    f"Application/build/test or unclassified worker in repository: "
                    f"process {item.name} ({comm}); close it before cleanup",
                )
            for fd in (item / "fd").iterdir():
                try:
                    require(
                        not inside(os.readlink(fd)), f"Open target: process {item.name}"
                    )
                except FileNotFoundError:
                    pass
            try:
                require(
                    not inside(os.readlink(item / "exe")),
                    f"Active target executable: {item.name}",
                )
                for line in (item / "maps").read_text().splitlines():
                    fields = line.split(maxsplit=5)
                    if len(fields) == 6:
                        require(
                            not inside(fields[5]), f"Mapped target: process {item.name}"
                        )
            except PermissionError:
                require(not is_tool, f"Cannot inspect relevant process {item.name}")
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            raise Refused(f"Cannot establish target inactivity for process {item.name}")


def erase_verified(root_fd, root, target, saved):
    """Use directory descriptors and O_NOFOLLOW; never recurse via a path symlink."""
    relative = target["path"]
    parts = components(root, relative)
    parent = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent
            )
            os.close(parent)
            parent = child

        def erase(directory_fd, name, rel):
            row = saved["entries"][rel]
            current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            require(
                identity(current) == row["stat"],
                "Target changed before deletion: " + rel,
            )
            if stat.S_ISDIR(current.st_mode):
                fd = os.open(
                    name,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )
                try:
                    require(identity(os.fstat(fd)) == row["stat"], "Directory replaced")
                    require(
                        sorted(os.listdir(fd)) == row["children"],
                        "Directory contents changed",
                    )
                    for child in row["children"]:
                        erase(fd, child, rel + "/" + child)
                    now = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                    require(
                        [now.st_dev, now.st_ino, now.st_mode] == row["stat"][:3],
                        "Directory replaced",
                    )
                    os.rmdir(name, dir_fd=directory_fd)
                finally:
                    os.close(fd)
            else:
                if stat.S_ISLNK(current.st_mode):
                    require(
                        os.readlink(name, dir_fd=directory_fd) == row["link"],
                        "Link changed",
                    )
                os.unlink(name, dir_fd=directory_fd)

        erase(parent, parts[-1], relative)
    finally:
        os.close(parent)


def validate(root, audit):
    require(root == root.resolve(), "Repository path is symlinked")
    require(
        [root.stat().st_dev, root.stat().st_ino] == audit["root_identity"],
        "Wrong repository root",
    )
    require(
        root.is_absolute() and stat.S_ISDIR((root / ".git").lstat().st_mode),
        "Missing Git metadata",
    )
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    require(head == audit["head"], "Repository HEAD changed; require new audit")
    if "index_stage_sha256" in audit:
        indexed = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "--stage", "-z"]
        )
        require(
            hashlib.sha256(indexed).hexdigest() == audit["index_stage_sha256"],
            "Git staging state changed; require new review",
        )
        tracked = [
            Path(os.fsdecode(entry.split(b"\t", 1)[1]))
            for entry in indexed.split(b"\0")
            if entry
        ]
        require(
            not any(
                path.is_relative_to(t["path"])
                for path in tracked
                for t in audit["targets"]
            ),
            "Deletion intersects tracked or staged material",
        )
    targets = [Path(t["path"]) for t in audit["targets"]]
    for index, target in enumerate(targets):
        require(
            all(
                not (target.is_relative_to(other) or other.is_relative_to(target))
                for other in targets[:index]
            ),
            "Overlapping deletion targets",
        )
        require(
            not any(Path(guard).is_relative_to(target) for guard in audit["guards"]),
            "Deletion intersects preserved source/document guard",
        )
    for relative, digest in audit["guards"].items():
        components(root, relative)
        p = root / relative
        require(
            p.is_file() and not p.is_symlink(), "Audit dependency changed: " + relative
        )
        with p.open("rb") as stream:
            require(
                hashlib.file_digest(stream, "sha256").hexdigest() == digest,
                "Audit dependency changed: " + relative,
            )
    snapshots = {}
    for t in audit["targets"]:
        mount_check(root, t["path"])
        try:
            current = snapshot(root, t["path"])
        except FileNotFoundError:
            require(
                not os.path.lexists(root / t["path"]),
                "Target changed during validation: " + t["path"],
            )
            snapshots[t["path"]] = None
            continue
        require(
            current["fingerprint"] == t["fingerprint"],
            "Changed target; retained: " + t["path"],
        )
        snapshots[t["path"]] = current
    return snapshots


def measure(root):
    """Allocated repository blocks and available bytes on its filesystem."""
    result = subprocess.check_output(
        ["du", "-sx", "-B1", "--", str(root)], text=True, timeout=60
    )
    return {
        "repository_allocated_bytes": int(result.split()[0]),
        "filesystem_available_bytes": shutil.disk_usage(root).free,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print/validate only; never ask or delete",
    )
    args = parser.parse_args()
    require(AUDIT is not None, "Audit not populated")
    root = Path(AUDIT["root"])
    snapshots = validate(root, AUDIT)
    assert_idle(root, AUDIT["targets"])
    initial_measurement = measure(root)
    print("Exact audited deletion preview (repository-relative paths):", flush=True)
    total = 0
    for t in AUDIT["targets"]:
        current = snapshots[t["path"]]
        allocated = current["allocated_bytes"] if current is not None else 0
        total += current["estimated_reclaim_bytes"] if current is not None else 0
        state = (
            "present, validated"
            if current is not None
            else "already absent; no reclaim"
        )
        print(
            f"{allocated:>12} allocated bytes  {t['path']}\n  {state}; {t['reason']}",
            flush=True,
        )
    print(
        f"Estimated reclaim: {total:,} bytes ({total / 2**30:.3f} GiB); "
        "shared blocks may reduce this.",
        flush=True,
    )
    print(
        "Current measurement: " + json.dumps(initial_measurement, sort_keys=True),
        flush=True,
    )
    print("Target and dependency validation PASS. No files deleted.", flush=True)
    if args.preview:
        return
    require(sys.stdin.isatty(), "Run interactively in your Ubuntu terminal")
    try:
        response = input("Type DELETE AUDITED TARGETS once to proceed: ")
    except EOFError as exc:
        raise Refused("Cancelled: end of input; no deletion") from exc
    require(
        response == "DELETE AUDITED TARGETS",
        "Cancelled",
    )
    confirmed = validate(root, AUDIT)
    require(
        not any(snapshots[p] is None and confirmed[p] is not None for p in snapshots),
        "Previously absent target appeared; require new review",
    )
    snapshots = confirmed
    assert_idle(root, AUDIT["targets"])
    before = measure(root)
    print("Before deletion: " + json.dumps(before, sort_keys=True), flush=True)
    removed = []
    absent = [p for p, snap in snapshots.items() if snap is None]
    fd = None
    current_target = None
    finished = False
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for t in AUDIT["targets"]:
            if snapshots[t["path"]] is None:
                print("Already absent; not reclaimed: " + t["path"], flush=True)
                continue
            current_target = t["path"]
            mount_check(root, t["path"])
            assert_idle(root, AUDIT["targets"])
            erase_verified(fd, root, t, snapshots[t["path"]])
            removed.append(t["path"])
            current_target = None
            print("Deleted: " + t["path"], flush=True)
        finished = True
    finally:
        unwinding = sys.exc_info()[0] is not None
        close_error = None
        if fd is not None:
            try:
                os.close(fd)
            except OSError as exc:
                close_error = type(exc).__name__
        measurement_error = None
        try:
            after = measure(root)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            after = None
            measurement_error = type(exc).__name__
        print(
            "Cleanup measurement: "
            + json.dumps(
                {
                    "before": before,
                    "after": after,
                    "deleted_paths": removed,
                    "already_absent_paths": absent,
                    "not_completed_paths": [
                        t["path"]
                        for t in AUDIT["targets"]
                        if t["path"] not in removed and t["path"] not in absent
                    ],
                    "interrupted_target_may_be_partial": current_target,
                    "complete": finished and after is not None and close_error is None,
                    "close_error_type": close_error,
                    "measurement_error_type": measurement_error,
                    "filesystem_available_change_bytes": (
                        after["filesystem_available_bytes"]
                        - before["filesystem_available_bytes"]
                    )
                    if after is not None
                    else None,
                    "note": "Concurrent unrelated writes/shared blocks affect free space",
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if (measurement_error or close_error) and not unwinding:
            raise Refused(
                "Final cleanup reporting failed: " + (measurement_error or close_error)
            )
    print("Finished. Kept all unlisted paths. No Git or host installation changes.")


if __name__ == "__main__":
    try:
        main()
    except (Refused, OSError, subprocess.SubprocessError) as exc:
        print("STOPPED: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("Stopped by owner; no automatic retry.", file=sys.stderr)
        raise SystemExit(130)
