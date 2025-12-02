from pathlib import Path # Для работы с путями
import os

# Конфигурация ресурсов
RESOURCE_DIR = Path.home() / "YamalPixelRes"
# Обновляем RESOURCES в начале кода
RESOURCES = {
    "logo.png": "https://disk.yandex.ru/i/XJ1rNloj-EcIGw",
    "logo1.png": "https://disk.yandex.ru/i/IazaA10AvflA2Q",
    "logo2.png": "https://disk.yandex.ru/i/X7VlJutjTuJI5g",
    "logo3.png": "https://disk.yandex.ru/i/aw_NY_pDSQ_yeg",
    "logo4.png": "https://disk.yandex.ru/i/qHwCeXH8SyMBqg",
    "logo5.png": "https://disk.yandex.ru/i/2ZbSia8Q4sPOmQ",
    "logo6.png": "https://disk.yandex.ru/i/9sk7fpOYULQe-w",
    "logo7.png": "https://disk.yandex.ru/i/Vks2YtorAoECdg",
    "logo8.png": "https://disk.yandex.ru/i/ztj5t0_y39yjcw",
    "menu_song.mp3": "https://disk.yandex.ru/d/Ahqnmj2T8YlNKg",
    "icon.ico": "https://disk.yandex.ru/i/nRwZp3AzRI16qQ"
}
# Конфигурация
CONFIG = {
    "version": "1.20.1",
    "fabric_loader": "0.17.2",
    "minecraft_dir": os.path.expanduser("~/YamalPixel"),
    "mods": [
        {
            "url": "https://disk.yandex.ru/d/aJHjc2LrzS8ndA",
            "file": "XaerosWorldMap_1.39.12_Fabric_1.20.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/UzM5BWOXB9S7OA",
            "file": "AdvancedReborn-1.20.1-1.2.9.jar",
        },
        # {'url': 'https://disk.yandex.ru/d/S_m78H3B-N9dCQ', 'file': 'pocket-repose-1.2.7-1.20.1.jar'},
        {
            "url": "https://disk.yandex.ru/d/c81POD3HZgp48Q",
            "file": "cc-tweaked-1.20.1-fabric-1.116.2.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/B48FGIIitm-olA",
            "file": "ae2-emi-crafting-1.3.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/YXPRt1scCMJ8kQ",
            "file": "antixray-fabric-1.4.6+1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/ukmqzaHQaTP03g",
            "file": "appliedenergistics2-fabric-15.4.9.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/aH-BHO05_WeuLw",
            "file": "architectury-9.2.14-fabric.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/fo5V3PpaLtZ-gw",
            "file": "areas-1.20.1-6.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/Tif04Xw7_kd8rQ",
            "file": "cardinal-components-api-5.2.3.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/k5xux5BX_T9-7g",
            "file": "choicetheorems-overhauled-village-friends-and-foes-add-on-1.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/378xaPNzlblGFA",
            "file": "cloth-config-11.1.136-fabric.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/5AivLjfk6Wgbog",
            "file": "collective-1.20.1-8.12.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/nSspzPB5G5ReWA",
            "file": "crafting_enchanted_golden_apple-1.0.0-fabric-1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/Ox5-1T4a9qkXHg",
            "file": "ctov-beautify-compat-2.0.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/o2kPxeHul4byng",
            "file": "emi-1.1.22+1.20.1+fabric.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/PNZi_54Tj4HP3Q",
            "file": "entityculling-fabric-1.9.1-mc1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/GNW5lwib5Xq9Eg",
            "file": "extra-mod-integrations-0.4.7+1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/EHHAo7HSzH2mmg",
            "file": "fabric-api-0.92.6+1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/IHBo3qyqAjR3fQ",
            "file": "fabric-language-kotlin-1.13.6+kotlin.2.2.20.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/r8gwsUQF7Wy9BQ",
            "file": "fallingleaves-1.15.6+1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/pddZ2W8za1yiSQ",
            "file": "indium-1.0.36+mc1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/PghcNlFWKcgSeg",
            "file": "InventoryProfilesNext-fabric-1.20-1.10.19.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/AZHbvFGGX_JAKQ",
            "file": "iris-1.7.6+mc1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/wwCGHqSxly5pXg",
            "file": "ironchests-5.0.2-fabric.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/OrlYw3O3rnSN1A",
            "file": "lambdynamiclights-4.4.0+1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/Sr4rPWBdFjEZfA",
            "file": "libIPN-fabric-1.20-4.0.2.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/7G3BPLxK1Dul1g",
            "file": "lithium-fabric-mc1.20.1-0.11.3.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/yE26wprToTM9hg",
            "file": "mavapi-1.1.4-mc1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/Po8eTPEwzDAOpg",
            "file": "mavm-1.2.6-mc1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/8luIo8Ygz83BEg",
            "file": "mcpitanlib-3.3.9-1.20.1-fabric.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/EsACr5Ex3R9Zdg",
            "file": "modmenu-badges-lib-2023.6.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/6CF52_F3QbnCzQ",
            "file": "noindium-1.1.0+1.20.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/B10LX8LVEZg0DQ",
            "file": "Patchouli-1.20.1-84.1-FABRIC.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/fCkZvVrEqlU3Rg",
            "file": "RebornCore-5.8.3.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/_CgYmn4OYeGnBQ",
            "file": "servercore-fabric-1.5.2+1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/uI7zlr5Yg-7skQ",
            "file": "sodium-extra-0.5.9+mc1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/Mft3dmbdbHjhHA",
            "file": "sodium-fabric-0.5.13+mc1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/dncEQy1PhTcgrw",
            "file": "TechReborn-5.8.3.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/_c-mQTKC4UB1cw",
            "file": "Terralith_1.20.x_v2.5.4.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/trH1NQ3Hw2QjXQ",
            "file": "Xaeros_Minimap_25.2.10_Fabric_1.20.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/H0dkq2G5XcrZFQ",
            "file": "moonlight-1.20-2.16.15-fabric.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/uXJYqfjy_aedHQ",
            "file": "immersive_weathering-1.20.1-2.0.5-fabric.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/5XOEqn8FkypWkg",
            "file": "create-fabric-6.0.8.0+build.1734-mc1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/XfzgIDOOzleiTA",
            "file": "create-structures-0.1.1-1.20.1-FABRIC.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/fMv6pNJFcHOKkA",
            "file": "createaddition-fabric+1.20.1-1.3.3.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/E_jBP9cQfeVX6g",
            "file": "Steam_Rails-1.6.14-beta+fabric-mc1.20.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/2bh0oqQsq4INXg",
            "file": "botarium-fabric-1.20.1-2.3.4.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/7ebHrjGobc89Og",
            "file": "travelersbackpack-fabric-1.20.1-9.1.41.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/P2yhjpE96GaH1Q",
            "file": "carryon-fabric-1.20.1-2.1.2.7.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/g33-cksFAVrbmg",
            "file": "treeharvester-1.20.1-9.1.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/tG9ulUDXHr53vQ",
            "file": "framework-fabric-1.20.1-0.7.15.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/lePC1Exc3PrWQA",
            "file": "refurbished_furniture-fabric-1.20.1-1.0.20.jar",
        },
        {
            "url": "https://disk.yandex.ru/d/_JyuGFFBszGFog",
            "file": "create_structures_arise-156.29.28-fabric-1.20.1.jar",
        },
    ],
}


# Конфигурация шейдеров
SHADERS_CONFIG = {
    "shaders": [
        {
            "name": "Aurora Shaders",
            "url": "https://disk.yandex.ru/d/AXeR74NrLMDpMw",
            "file": "Aurora-s-Shaders-1.20.2-1.20.zip",
        },
        {
            "name": "BSL Shaders",
            "url": "https://disk.yandex.ru/d/G7YX0Az5ZuUptA",
            "file": "BSL_v8.4.01.2.zip",
        },
        {
            "name": "Bliss Shaders",
            "url": "https://disk.yandex.ru/d/GjbXRVgDF9S55w",
            "file": "Bliss_v2.0.4_(Chocapic13_Shaders_edit).zip",
        },
        {
            "name": "Complementary Reimagined",
            "url": "https://disk.yandex.ru/d/1afdG-63Z4dxog",
            "file": "ComplementaryReimagined_r5.0.1.zip",
        },
        {
            "name": "Complementary Unbound",
            "url": "https://disk.yandex.ru/d/mPKPzpM5Rfw4Ag",
            "file": "ComplementaryUnbound_r5.1.1.zip",
        },
        {
            "name": "Hysteria Shaders",
            "url": "https://disk.yandex.ru/d/-sJWGfa1wzA77w",
            "file": "Hysteria-Shaders-Universal-v1.1.0.zip",
        },
        {
            "name": "Insanity Shader",
            "url": "https://disk.yandex.ru/d/fu3X8ZJ1FdyfWQ",
            "file": "Insanity-Shader-Universal-v1.500.zip",
        },
        {
            "name": "IterationT Shaders",
            "url": "https://disk.yandex.ru/d/U4ZsdD303pamBg",
            "file": "IterationT-Shaders-v2.0.0-All-Versions.zip",
        },
        {
            "name": "Kappa Shaders",
            "url": "https://disk.yandex.ru/d/salUSNvQg01C0A",
            "file": "Kappa_v5.2.zip",
        },
        {
            "name": "Lost Souls",
            "url": "https://disk.yandex.ru/d/XydaLzVyWPOeFg",
            "file": "Lost Souls version ComplementaryReimagined_r5.2.1.zip",
        },
        {
            "name": "MakeUp UltraFast",
            "url": "https://disk.yandex.ru/d/lXzHIs0K3Ico0Q",
            "file": "MakeUp-UltraFast-8.9d.zip",
        },
        {
            "name": "SEUS Renewed",
            "url": "https://disk.yandex.ru/d/yPiGbWFPYdfcqA",
            "file": "SEUS-Renewed-1.0.0.zip",
        },
        {
            "name": "Sildur Vibrant Shaders",
            "url": "https://disk.yandex.ru/d/258c6NIYVdugWw",
            "file": "Sildur's Vibrant Shaders v1.32 Extreme.zip",
        },
        {
            "name": "Solas Shader",
            "url": "https://disk.yandex.ru/d/z-tQHGTsiwQAhg",
            "file": "Solas Shader V2.0 [BETA 0.6b].zip",
        },
        {
            "name": "Spooklementary",
            "url": "https://disk.yandex.ru/d/AjAhhGl1ueGdsQ",
            "file": "Spooklementary_1.1.zip",
        },
        {
            "name": "VanillAA",
            "url": "https://disk.yandex.ru/d/NErUzx0Q6ZCgew",
            "file": "VanillAA.zip",
        },
        {
            "name": "Ymir Shader",
            "url": "https://disk.yandex.ru/d/IOv8qwrvYktaJQ",
            "file": "Ymir_beta3.0.zip",
        },
        {
            "name": "Miniature Shader",
            "url": "https://disk.yandex.ru/d/dNcMKdHzP1cFRQ",
            "file": "miniature-shader-2.14.1.zip",
        },
        {
            "name": "Nostalgia Shader",
            "url": "https://disk.yandex.ru/d/QwLrr-DRx2k8tw",
            "file": "nostalgia_v5.0.zip",
        },
        {
            "name": "Photon Shader",
            "url": "https://disk.yandex.ru/d/JNOA4ITKiqA04g",
            "file": "photon-iris-stable.zip",
        },
        {
            "name": "Rethinking Voxels",
            "url": "https://disk.yandex.ru/d/3SUoopowIUI8pA",
            "file": "rethinking-voxels_beta18c.zip",
        },
        {
            "name": "Super Duper Vanilla",
            "url": "https://disk.yandex.ru/d/aEiGZvEBXRe67Q",
            "file": "superDuperVanilla.zip",
        },
    ]
}

essential_mods = [
                {
                    "url": "https://disk.yandex.ru/d/aJHjc2LrzS8ndA",
                    "file": "XaerosWorldMap_1.39.12_Fabric_1.20.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/UzM5BWOXB9S7OA",
                    "file": "AdvancedReborn-1.20.1-1.2.9.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/B48FGIIitm-olA",
                    "file": "ae2-emi-crafting-1.3.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/YXPRt1scCMJ8kQ",
                    "file": "antixray-fabric-1.4.6+1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/ukmqzaHQaTP03g",
                    "file": "appliedenergistics2-fabric-15.4.9.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/aH-BHO05_WeuLw",
                    "file": "architectury-9.2.14-fabric.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/fo5V3PpaLtZ-gw",
                    "file": "areas-1.20.1-6.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/Tif04Xw7_kd8rQ",
                    "file": "cardinal-components-api-5.2.3.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/k5xux5BX_T9-7g",
                    "file": "choicetheorems-overhauled-village-friends-and-foes-add-on-1.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/378xaPNzlblGFA",
                    "file": "cloth-config-11.1.136-fabric.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/5AivLjfk6Wgbog",
                    "file": "collective-1.20.1-8.12.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/nSspzPB5G5ReWA",
                    "file": "crafting_enchanted_golden_apple-1.0.0-fabric-1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/Ox5-1T4a9qkXHg",
                    "file": "ctov-beautify-compat-2.0.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/o2kPxeHul4byng",
                    "file": "emi-1.1.22+1.20.1+fabric.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/PNZi_54Tj4HP3Q",
                    "file": "entityculling-fabric-1.9.1-mc1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/GNW5lwib5Xq9Eg",
                    "file": "extra-mod-integrations-0.4.7+1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/EHHAo7HSzH2mmg",
                    "file": "fabric-api-0.92.6+1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/IHBo3qyqAjR3fQ",
                    "file": "fabric-language-kotlin-1.13.6+kotlin.2.2.20.jarr",
                },
                {
                    "url": "https://disk.yandex.ru/d/r8gwsUQF7Wy9BQ",
                    "file": "fallingleaves-1.15.6+1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/pddZ2W8za1yiSQ",
                    "file": "indium-1.0.36+mc1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/PghcNlFWKcgSeg",
                    "file": "InventoryProfilesNext-fabric-1.20-1.10.19.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/AZHbvFGGX_JAKQ",
                    "file": "iris-1.7.6+mc1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/wwCGHqSxly5pXg",
                    "file": "ironchests-5.0.2-fabric.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/OrlYw3O3rnSN1A",
                    "file": "lambdynamiclights-4.4.0+1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/Sr4rPWBdFjEZfA",
                    "file": "libIPN-fabric-1.20-4.0.2.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/7G3BPLxK1Dul1g",
                    "file": "lithium-fabric-mc1.20.1-0.11.3.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/yE26wprToTM9hg",
                    "file": "mavapi-1.1.4-mc1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/Po8eTPEwzDAOpg",
                    "file": "mavm-1.2.6-mc1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/8luIo8Ygz83BEg",
                    "file": "mcpitanlib-3.3.9-1.20.1-fabric.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/EsACr5Ex3R9Zdg",
                    "file": "modmenu-badges-lib-2023.6.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/6CF52_F3QbnCzQ",
                    "file": "noindium-1.1.0+1.20.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/B10LX8LVEZg0DQ",
                    "file": "Patchouli-1.20.1-84.1-FABRIC.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/fCkZvVrEqlU3Rg",
                    "file": "RebornCore-5.8.3.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/_CgYmn4OYeGnBQ",
                    "file": "servercore-fabric-1.5.2+1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/uI7zlr5Yg-7skQ",
                    "file": "sodium-extra-0.5.9+mc1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/Mft3dmbdbHjhHA",
                    "file": "sodium-fabric-0.5.13+mc1.20.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/dncEQy1PhTcgrw",
                    "file": "TechReborn-5.8.3.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/_c-mQTKC4UB1cw",
                    "file": "Terralith_1.20.x_v2.5.4.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/trH1NQ3Hw2QjXQ",
                    "file": "Xaeros_Minimap_25.2.10_Fabric_1.20.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/7ebHrjGobc89Og",
                    "file": "travelersbackpack-fabric-1.20.1-9.1.41.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/P2yhjpE96GaH1Q",
                    "file": "carryon-fabric-1.20.1-2.1.2.7.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/g33-cksFAVrbmg",
                    "file": "treeharvester-1.20.1-9.1.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/tG9ulUDXHr53vQ",
                    "file": "framework-fabric-1.20.1-0.7.15.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/lePC1Exc3PrWQA",
                    "file": "refurbished_furniture-fabric-1.20.1-1.0.20.jar",
                },
                {
                    "url": "https://disk.yandex.ru/d/_JyuGFFBszGFog",
                    "file": "create_structures_arise-156.29.28-fabric-1.20.1.jar",
                },
            ]

def get_minecraft_version(version_name):
    if version_name.startswith("📦 "):
        try:
            # Пробуем получить информацию из JSON файла сборки
            import json
            import os

            collection_name = version_name[2:]
            collections_dir = COLLECTIONS_CONFIG["collections_dir"]

            if os.path.exists(collections_dir):
                for filename in os.listdir(collections_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(collections_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        if data.get('name') == collection_name:
                            return data.get('minecraft_version', '1.21.1')
        except:
            pass
    """Получает версию Minecraft для выбранной версии"""
    version_map = {
        "YamalPixel": "1.20.1",
        "Minecraft 1.12.2": "1.12.2",
        "Minecraft 1.12.2 + Fabric": "1.12.2",
        "Minecraft 1.12.2 + Forge": "1.12.2",
        "Minecraft 1.12.2 + Quilt": "1.12.2",

        "Minecraft 1.14.4": "1.14.4",
        "Minecraft 1.14.4 + Fabric": "1.14.4",
        "Minecraft 1.14.4 + Forge": "1.14.4",
        "Minecraft 1.14.4 + Quilt": "1.14.4",

        "Minecraft 1.15.2": "1.15.2",
        "Minecraft 1.15.2 + Fabric": "1.15.2",
        "Minecraft 1.15.2 + Forge": "1.15.2",
        "Minecraft 1.15.2 + Quilt": "1.15.2",

        "Minecraft 1.16.5": "1.16.5",
        "Minecraft 1.16.5 + Fabric": "1.16.5",
        "Minecraft 1.16.5 + Forge": "1.16.5",
        "Minecraft 1.16.5 + Quilt": "1.16.5",

        "Minecraft 1.17.1": "1.17.1",
        "Minecraft 1.17.1 + Fabric": "1.17.1",
        "Minecraft 1.17.1 + Forge": "1.17.1",
        "Minecraft 1.17.1 + Quilt": "1.17.1",

        "Minecraft 1.18.2": "1.18.2",
        "Minecraft 1.18.2 + Fabric": "1.18.2",
        "Minecraft 1.18.2 + Forge": "1.18.2",
        "Minecraft 1.18.2 + Quilt": "1.18.2",

        "Minecraft 1.19.2": "1.19.2",
        "Minecraft 1.19.2 + Fabric": "1.19.2",
        "Minecraft 1.19.2 + Forge": "1.19.2",
        "Minecraft 1.19.2 + Quilt": "1.19.2",

        "Minecraft 1.20.1": "1.20.1",
        "Minecraft 1.20.1 + Fabric": "1.20.1",
        "Minecraft 1.20.1 + Forge": "1.20.1",
        "Minecraft 1.20.1 + Quilt": "1.20.1",
        "Minecraft 1.20.1 + NeoForge": "1.20.1",

        "Minecraft 1.20.2": "1.20.2",
        "Minecraft 1.20.2 + Fabric": "1.20.2",
        "Minecraft 1.20.2 + Forge": "1.20.2",
        "Minecraft 1.20.2 + Quilt": "1.20.2",
        "Minecraft 1.20.2 + NeoForge": "1.20.2",

        "Minecraft 1.20.3": "1.20.3",
        "Minecraft 1.20.3 + Fabric": "1.20.3",
        "Minecraft 1.20.3 + Forge": "1.20.3",
        "Minecraft 1.20.3 + Quilt": "1.20.3",
        "Minecraft 1.20.3 + NeoForge": "1.20.3",

        "Minecraft 1.20.4": "1.20.4",
        "Minecraft 1.20.4 + Fabric": "1.20.4",
        "Minecraft 1.20.4 + Forge": "1.20.4",
        "Minecraft 1.20.4 + Quilt": "1.20.4",
        "Minecraft 1.20.4 + NeoForge": "1.20.4",

        "Minecraft 1.20.5": "1.20.5",
        "Minecraft 1.20.5 + Fabric": "1.20.5",
        "Minecraft 1.20.5 + Forge": "1.20.5",
        "Minecraft 1.20.5 + Quilt": "1.20.5",
        "Minecraft 1.20.5 + NeoForge": "1.20.5",

        "Minecraft 1.20.6": "1.20.6",
        "Minecraft 1.20.6 + Fabric": "1.20.6",
        "Minecraft 1.20.6 + Forge": "1.20.6",
        "Minecraft 1.20.6 + Quilt": "1.20.6",
        "Minecraft 1.20.6 + NeoForge": "1.20.6",

        "Minecraft 1.21": "1.21",
        "Minecraft 1.21 + Fabric": "1.21",
        "Minecraft 1.21 + Forge": "1.21",
        "Minecraft 1.21 + Quilt": "1.21",
        "Minecraft 1.21 + NeoForge": "1.21",

        "Minecraft 1.21.1": "1.21.1",
        "Minecraft 1.21.1 + Fabric": "1.21.1",
        "Minecraft 1.21.1 + Forge": "1.21.1",
        "Minecraft 1.21.1 + Quilt": "1.21.1",
        "Minecraft 1.21.1 + NeoForge": "1.21.1",

        "Minecraft 1.21.2": "1.21.2",
        "Minecraft 1.21.2 + Fabric": "1.21.2",
        "Minecraft 1.21.2 + Forge": "1.21.2",
        "Minecraft 1.21.2 + Quilt": "1.21.2",
        "Minecraft 1.21.2 + NeoForge": "1.21.2",

        "Minecraft 1.21.3": "1.21.3",
        "Minecraft 1.21.3 + Fabric": "1.21.3",
        "Minecraft 1.21.3 + Forge": "1.21.3",
        "Minecraft 1.21.3 + Quilt": "1.21.3",
        "Minecraft 1.21.3 + NeoForge": "1.21.3",

        "Minecraft 1.21.4": "1.21.4",
        "Minecraft 1.21.4 + Fabric": "1.21.4",
        "Minecraft 1.21.4 + Forge": "1.21.4",
        "Minecraft 1.21.4 + Quilt": "1.21.4",
        "Minecraft 1.21.4 + NeoForge": "1.21.4",
    }

    return version_map.get(version_name, "1.20.1")


version_configs = {
    "YamalPixel": ("1.20.1", "fabric", "0.17.2"),
    "Minecraft 1.12.2": ("1.12.2", None, None),
    "Minecraft 1.12.2 + Fabric": ("1.12.2", "fabric", "0.17.2"),
    "Minecraft 1.12.2 + Forge": ("1.12.2", "forge", "latest"),
    "Minecraft 1.12.2 + Quilt": ("1.12.2", "quilt", None),

    "Minecraft 1.14.4": ("1.14.4", None, None),
    "Minecraft 1.14.4 + Fabric": ("1.14.4", "fabric", "0.17.2"),
    "Minecraft 1.14.4 + Forge": ("1.14.4", "forge", "latest"),
    "Minecraft 1.14.4 + Quilt": ("1.14.4", "quilt", None),


    "Minecraft 1.15.2": ("1.15.2", None, None),
    "Minecraft 1.15.2 + Fabric": ("1.15.2", "fabric", "0.17.2"),
    "Minecraft 1.15.2 + Forge": ("1.15.2", "forge", "latest"),
    "Minecraft 1.15.2 + Quilt": ("1.15.2", "quilt", None),


    "Minecraft 1.16.5": ("1.16.5", None, None),
    "Minecraft 1.16.5 + Fabric": ("1.16.5", "fabric", "0.17.2"),
    "Minecraft 1.16.5 + Forge": ("1.16.5", "forge", "latest"),
    "Minecraft 1.16.5 + Quilt": ("1.16.5", "quilt", None),

    "Minecraft 1.17.1": ("1.17.1", None, None),
    "Minecraft 1.17.1 + Fabric": ("1.17.1", "fabric", "0.17.2"),
    "Minecraft 1.17.1 + Forge": ("1.17.1", "forge", "latest"),
    "Minecraft 1.17.1 + Quilt": ("1.17.1", "quilt", None),


    "Minecraft 1.18.2": ("1.18.2", None, None),
    "Minecraft 1.18.2 + Fabric": ("1.18.2", "fabric", "0.17.2"),
    "Minecraft 1.18.2 + Forge": ("1.18.2", "forge", "latest"),
    "Minecraft 1.18.2 + Quilt": ("1.18.2", "quilt", None),


    "Minecraft 1.19.2": ("1.19.2", None, None),
    "Minecraft 1.19.2 + Fabric": ("1.19.2", "fabric", "0.17.2"),
    "Minecraft 1.19.2 + Forge": ("1.19.2", "forge", "latest"),
    "Minecraft 1.19.2 + Quilt": ("1.19.2", "quilt", None),


    "Minecraft 1.20.1": ("1.20.1", None, None),
    "Minecraft 1.20.1 + Fabric": ("1.20.1", "fabric", "0.17.2"),
    "Minecraft 1.20.1 + Forge": ("1.20.1", "forge", "latest"),
    "Minecraft 1.20.1 + Quilt": ("1.20.1", "quilt", None),

    "Minecraft 1.20.2": ("1.20.2", None, None),
    "Minecraft 1.20.2 + Fabric": ("1.20.2", "fabric", "0.17.2"),
    "Minecraft 1.20.2 + Forge": ("1.20.2", "forge", "latest"),
    "Minecraft 1.20.2 + Quilt": ("1.20.2", "quilt", None),
    "Minecraft 1.20.2 + NeoForge": ("1.20.2", "neoforge", None),

    "Minecraft 1.20.3": ("1.20.3", None, None),
    "Minecraft 1.20.3 + Fabric": ("1.20.3", "fabric", "0.17.2"),
    "Minecraft 1.20.3 + Forge": ("1.20.3", "forge", "latest"),
    "Minecraft 1.20.3 + Quilt": ("1.20.3", "quilt", None),
    "Minecraft 1.20.3 + NeoForge": ("1.20.3", "neoforge", None),

    "Minecraft 1.20.4": ("1.20.4", None, None),
    "Minecraft 1.20.4 + Fabric": ("1.20.4", "fabric", "0.17.2"),
    "Minecraft 1.20.4 + Forge": ("1.20.4", "forge", "latest"),
    "Minecraft 1.20.4 + Quilt": ("1.20.4", "quilt", None),
    "Minecraft 1.20.4 + NeoForge": ("1.20.4", "neoforge", None),

    "Minecraft 1.20.5": ("1.20.5", None, None),
    "Minecraft 1.20.5 + Fabric": ("1.20.5", "fabric", "0.17.2"),
    "Minecraft 1.20.5 + Forge": ("1.20.5", "forge", "latest"),
    "Minecraft 1.20.5 + Quilt": ("1.20.5", "quilt", None),
    "Minecraft 1.20.5 + NeoForge": ("1.20.5", "neoforge", None),

    "Minecraft 1.20.6": ("1.20.6", None, None),
    "Minecraft 1.20.6 + Fabric": ("1.20.6", "fabric", "0.17.2"),
    "Minecraft 1.20.6 + Forge": ("1.20.6", "forge", "latest"),
    "Minecraft 1.20.6 + Quilt": ("1.20.6", "quilt", None),
    "Minecraft 1.20.6 + NeoForge": ("1.20.6", "neoforge", None),


    "Minecraft 1.21": ("1.21", None, None),
    "Minecraft 1.21 + Fabric": ("1.21", "fabric", "0.17.2"),
    "Minecraft 1.21 + Forge": ("1.21", "forge", "latest"),
    "Minecraft 1.21 + Quilt": ("1.21", "quilt", None),
    "Minecraft 1.21 + NeoForge": ("1.21", "neoforge", None),

    "Minecraft 1.21.1": ("1.21.1", None, None),
    "Minecraft 1.21.1 + Fabric": ("1.21.1", "fabric", "0.17.2"),
    "Minecraft 1.21.1 + Forge": ("1.21.1", "forge", "latest"),
    "Minecraft 1.21.1 + Quilt": ("1.21.1", "quilt", None),
    "Minecraft 1.21.1 + NeoForge": ("1.21.1", "neoforge", None),

    "Minecraft 1.21.2": ("1.21.2", None, None),
    "Minecraft 1.21.2 + Fabric": ("1.21.2", "fabric", "0.17.2"),
    "Minecraft 1.21.2 + Forge": ("1.21.2", "forge", "latest"),
    "Minecraft 1.21.2 + Quilt": ("1.21.2", "quilt", None),
    "Minecraft 1.21.2 + NeoForge": ("1.21.2", "neoforge", None),

    "Minecraft 1.21.3": ("1.21.3", None, None),
    "Minecraft 1.21.3 + Fabric": ("1.21.3", "fabric", "0.17.2"),
    "Minecraft 1.21.3 + Forge": ("1.21.3", "forge", "latest"),
    "Minecraft 1.21.3 + Quilt": ("1.21.3", "quilt", None),
    "Minecraft 1.21.3 + NeoForge": ("1.21.3", "neoforge", None),


    "Minecraft 1.21.4": ("1.21.4", None, None),
    "Minecraft 1.21.4 + Fabric": ("1.21.4", "fabric", "0.17.2"),
    "Minecraft 1.21.4 + Forge": ("1.21.4", "forge", "latest"),
    "Minecraft 1.21.4 + Quilt": ("1.21.4", "quilt", None),
    "Minecraft 1.21.4 + NeoForge": ("1.21.4", "neoforge", None),
}


QUILT_CONFIG = {
    "supported_versions": ["1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2", "1.19.2", "1.20.1", "1.20.2", "1.20.3", "1.20.4", "1.20.5", "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"]
}

import json
import os
from datetime import datetime

USER_COLLECTIONS_DIR = os.path.join(CONFIG["minecraft_dir"], "custom_collections")
os.makedirs(USER_COLLECTIONS_DIR, exist_ok=True)


def load_user_collections():
    """Загружает все пользовательские сборки"""
    collections = []

    if not os.path.exists(USER_COLLECTIONS_DIR):
        return collections

    for filename in os.listdir(USER_COLLECTIONS_DIR):
        if filename.endswith('.json'):
            try:
                filepath = os.path.join(USER_COLLECTIONS_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Проверяем обязательные поля
                if all(key in data for key in ['name', 'minecraft_version', 'loader']):
                    collections.append({
                        'name': data['name'],
                        'filename': filename,
                        'minecraft_version': data['minecraft_version'],
                        'loader': data['loader'],
                        'loader_version': data.get('loader_version'),
                        'mods': data.get('mods', []),
                        'mod_count': len(data.get('mods', [])),
                        'created_at': data.get('created_at', datetime.now().isoformat()),
                        'description': data.get('description', '')
                    })
            except Exception as e:
                print(f"⚠️ Ошибка загрузки сборки {filename}: {e}")

    return collections


def save_user_collection(collection_data):
    """Сохраняет пользовательскую сборку"""
    try:
        # Создаем безопасное имя файла
        safe_name = "".join(c for c in collection_data['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name[:50]

        filename = f"{safe_name}.json"
        filepath = os.path.join(USER_COLLECTIONS_DIR, filename)

        # Добавляем метаданные
        collection_data['created_at'] = datetime.now().isoformat()
        collection_data['updated_at'] = datetime.now().isoformat()

        # Сохраняем файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, indent=2, ensure_ascii=False)

        return True, filename
    except Exception as e:
        return False, str(e)


def delete_user_collection(collection_name):
    """Удаляет пользовательскую сборку"""
    try:
        # Ищем файл по имени сборки
        for filename in os.listdir(USER_COLLECTIONS_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(USER_COLLECTIONS_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if data.get('name') == collection_name:
                    os.remove(filepath)
                    return True

        return False
    except Exception as e:
        print(f"❌ Ошибка удаления сборки: {e}")
        return False

COLLECTIONS_CONFIG = {
    "collections_dir": os.path.join(CONFIG["minecraft_dir"], "collections")
}

messages = [
        "Удачи! (она тебе понадобится)",
        "Не удивляйся если всё сломается!",
        "Твой компьютер уже ненавидит тебя...",
        "Помни: это твой выбор!",
        "RIP твоему FPS.",
        "Скажи привет майнеру.",
        "Спасибо за удаленный доступ.",
        "Ого сколько у тебя денег...Мало...",
        "Потрогай траву...",
        "А ты знаешь как выглядит небо?",
        "Выпил пива уже?",
        "Добро пожаловать!",
        "Люби аксолотлей.",
        "Может быть всё напрасно?",
        "У Артёмов нет детей.",
        "У меня есть дискорд сервер:)",
        "Sludge life тоже круто!",
        "Купи мне словарь Русского и Могучего!",
        "Твой FPS: да.",
        "Гречка дорожает, а ты в майнкрафт играешь...",
        "Пахнет жареным... (твой видеокартой)",
        "Системные требования: иметь систему (необязательно)",
        "Твой ПК: 🔥🔥🔥",
        "Запускаю криптоферму... шучу... наверное...",
        "Твоя мамка гордится тобой! (нет)",
        "Поздравляю! Ты 1000-й пользователь! (приз: вирус)",
        "Оптимизация? Не, не слышал.",
        "Добро пожаловать в ад, выбери свой котел!",
        "Твой скин такой же кринжовый, как и твой вкус",
        "Сервер просит не тыкать в него палкой",
        "Загрузка успешна! (это ложь)",
        "Ты знал что трава зеленая? Вот и я нет",
        "Рекомендуется: выключить монитор для лучшего FPS",
        "Твои моды конфликтуют сильнее, чем родители в разводе",
        "Чиним неисправность... шучу, идем пить чай",
        "Это не баг, это фича (ха-ха)",
        "Твой процессор плачет кровавыми слезами",
        "Памяти: мало. Проблем: много. Настроение: ахуенно",
        "Запускаю NASA... ой, это же майнкрафт",
        "Твоя видеокарта: 💀 RIP 💀",
        "Совет: не дыши на компьютер, он пугается",
        "Готовься к слайд-шоу вместо игры!",
        "Твои настройки графики: УЛЬТРА КРИНЖ",
        "Модпак загружен! (и твоя душа продана)",
        "Добро пожаловать в цифровой дурдом!",
        "Твой логин: анон. Пароль: ******** (все равно '12345')",
        "Система: работает. Разум: на перезагрузке",
        "Запускаю... стоп, а что это за кнопка?",
        "Все сломалось! Шучу... пока что...",
        "Твоя ОС: Windows (мне жаль)",
        "Рекомендуемое время игры: никогда",
        "Чекни свой FPS: ㋡ ㋡ ㋡ (это смайлики, не цифры)",
        "Твоя сборка модов: шедевр (психбольницы)",
        "Готово! Теперь можешь идти плакать в угол",
        "Установка завершена! (шутка, это только начало)",
        "Добро пожаловать в симулятор слабого ПК!",
        "Твоя мышь: жирная. Клавиатура: липкая. Настроение: gaming",
        "Запускаю... ой, подожди, нужно перекреститься",
        "Системные требования: терпение и алкоголь",
        "Твой ПК издает звуки? Это нормально! (нет)",
        "Готово! Теперь ты официально NEET",
        "Оптимизация проведена! (на самом деле нет)",
        "Добро пожаловать в адскую вечеринку FPS-дропов!",
        "Твоя сборка: 'ахуенная' (с) твоя мамка",
        "Все работает! (это временно)",
        "Загрузка... пока можешь сходить в душ",
        "Твой RAM: 💀 УБИТ 💀",
        "Привет от разработчика: иди нахуй <3",
        "Готово! Время играть... или нет?",
        "Система: загружена. Санity: не найдена",
        "Твоя игра теперь с DLC: 'баги и кринж'",
        "Добро пожаловать в симулятор ожидания!",
        "Все сломалось! Ахаха, расслабился? Шучу... наверное...",
        "Твой ПК теперь обогреватель! (бесплатно!)",
        "Готово! Наслаждайся слайд-шоу!",
        "Рекомендация: не смотри на FPS-счетчик",
        "Твоя видеокарта: 🔥 ГОРИТ 🔥 (в переносном смысле)",
        "Запуск успешен! (если успех = боль)",
        "Добро пожаловать в клуб 'У меня все тормозит!'",
        "Твои настройки: УЛЬТРА НИЗКИЕ (как твоя самооценка)",
        "Система: работает. Мозг: нет.",
        "Все готово! Теперь можешь идти за пивом",
        "Твой ПК издает странные звуки? Это фича!",
        "Готово! Время играть... или переустанавливать Windows?",
        "Добро пожаловать в ад! Выбери свой грех:",
        "- Кринжовые моды",
        "- Убитый FPS",
        "- Выжженная видеокарта",
        "Твоя сборка: 'я сам это собирал' (ошибка)",
        "Все работает! (пока не тронешь)",
        "Загрузка завершена! Теперь можно грузить моды...",
        "Твой CPU: 💯% (это плохо)",
        "Готово! Наслаждайся пикселями!",
        "Добро пожаловать в симулятор слабоумия!",
        "Твоя ОС: кринж. Железо: боль. Настроение: gaming",
        "Все сломалось! (шучу, все сломалось потом)",
        "Система: загружена. Проблемы: загружены тоже",
        "Твоя игра теперь с RTX! (шучу, у тебя GT 210)",
        "Готово! Время для... ой, все зависло",
        "Добро пожаловать в клуб 'Я 5 часов настраивал лаунчер'",
        "Твой ПК: 💸 ДЕНЬГИ НА ВЕТЕР 💸",
        "Все работает! (на старом ПК в музее)",
        "Запуск: успешен! FPS: провален! Настроение: ахуенно!",
        "Добро пожаловать в дикий запад багов и глитчей!",
        "Твоя сборка: 'оно как-то само'",
        "Готово! Теперь можешь идти гуглить 'почему все тормозит'",
        "Система: работает. Нервы: нет.",
        "Твой FPS: ❤️ ЛЮБОВЬ ❤️ (к слайд-шоу)",
        "Все сломалось! Ахаха... стоп, это не шутка...",
        "Добро пожаловать в адскую вечеринку глитчей!",
        "Твоя видеокарта: 💀 ОТДЫХАЕТ 💀 (навсегда)",
        "Готово! Наслаждайся... ой, синий экран...",
        "Сервак запущен, а ты - опущен",
    ]