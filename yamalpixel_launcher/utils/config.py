import json
import os
from pathlib import Path
from typing import Dict, Any, List


class Config:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.default_config = self._get_default_config()
        self.data = self._load_config()

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "version": "1.20.1",
            "fabric_loader": "0.16.10",
            "minecraft_dir": str(Path.home() / "YamalPixel"),
            "jvm_memory": "4G",
            "mods": [
                {"url": "https://disk.yandex.ru/d/aJHjc2LrzS8ndA", "file": "XaerosWorldMap_1.39.12_Fabric_1.20.jar"},
                {"url": "https://disk.yandex.ru/d/UzM5BWOXB9S7OA", "file": "AdvancedReborn-1.20.1-1.2.9.jar"},
                {"url": "https://disk.yandex.ru/d/c81POD3HZgp48Q", "file": "cc-tweaked-1.20.1-fabric-1.116.2.jar"},
                {"url": "https://disk.yandex.ru/d/B48FGIIitm-olA", "file": "ae2-emi-crafting-1.3.1.jar"},
                {"url": "https://disk.yandex.ru/d/YXPRt1scCMJ8kQ", "file": "antixray-fabric-1.4.6+1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/ukmqzaHQaTP03g", "file": "appliedenergistics2-fabric-15.4.9.jar"},
                {"url": "https://disk.yandex.ru/d/aH-BHO05_WeuLw", "file": "architectury-9.2.14-fabric.jar"},
                {"url": "https://disk.yandex.ru/d/fo5V3PpaLtZ-gw", "file": "areas-1.20.1-6.1.jar"},
                {"url": "https://disk.yandex.ru/d/Tif04Xw7_kd8rQ", "file": "cardinal-components-api-5.2.3.jar"},
                {"url": "https://disk.yandex.ru/d/k5xux5BX_T9-7g",
                 "file": "choicetheorems-overhauled-village-friends-and-foes-add-on-1.1.jar"},
                {"url": "https://disk.yandex.ru/d/378xaPNzlblGFA", "file": "cloth-config-11.1.136-fabric.jar"},
                {"url": "https://disk.yandex.ru/d/5AivLjfk6Wgbog", "file": "collective-1.20.1-8.12.jar"},
                {"url": "https://disk.yandex.ru/d/nSspzPB5G5ReWA",
                 "file": "crafting_enchanted_golden_apple-1.0.0-fabric-1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/Ox5-1T4a9qkXHg", "file": "ctov-beautify-compat-2.0.jar"},
                {"url": "https://disk.yandex.ru/d/o2kPxeHul4byng", "file": "emi-1.1.22+1.20.1+fabric.jar"},
                {"url": "https://disk.yandex.ru/d/PNZi_54Tj4HP3Q", "file": "entityculling-fabric-1.9.1-mc1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/GNW5lwib5Xq9Eg", "file": "extra-mod-integrations-0.4.7+1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/EHHAo7HSzH2mmg", "file": "fabric-api-0.92.6+1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/IHBo3qyqAjR3fQ",
                 "file": "fabric-language-kotlin-1.13.6+kotlin.2.2.20.jar"},
                {"url": "https://disk.yandex.ru/d/r8gwsUQF7Wy9BQ", "file": "fallingleaves-1.15.6+1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/pddZ2W8za1yiSQ", "file": "indium-1.0.36+mc1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/PghcNlFWKcgSeg",
                 "file": "InventoryProfilesNext-fabric-1.20-1.10.19.jar"},
                {"url": "https://disk.yandex.ru/d/AZHbvFGGX_JAKQ", "file": "iris-1.7.6+mc1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/wwCGHqSxly5pXg", "file": "ironchests-5.0.2-fabric.jar"},
                {"url": "https://disk.yandex.ru/d/OrlYw3O3rnSN1A", "file": "lambdynamiclights-4.4.0+1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/Sr4rPWBdFjEZfA", "file": "libIPN-fabric-1.20-4.0.2.jar"},
                {"url": "https://disk.yandex.ru/d/7G3BPLxK1Dul1g", "file": "lithium-fabric-mc1.20.1-0.11.3.jar"},
                {"url": "https://disk.yandex.ru/d/yE26wprToTM9hg", "file": "mavapi-1.1.4-mc1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/Po8eTPEwzDAOpg", "file": "mavm-1.2.6-mc1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/8luIo8Ygz83BEg", "file": "mcpitanlib-3.3.9-1.20.1-fabric.jar"},
                {"url": "https://disk.yandex.ru/d/EsACr5Ex3R9Zdg", "file": "modmenu-badges-lib-2023.6.1.jar"},
                {"url": "https://disk.yandex.ru/d/6CF52_F3QbnCzQ", "file": "noindium-1.1.0+1.20.jar"},
                {"url": "https://disk.yandex.ru/d/B10LX8LVEZg0DQ", "file": "Patchouli-1.20.1-84.1-FABRIC.jar"},
                {"url": "https://disk.yandex.ru/d/fCkZvVrEqlU3Rg", "file": "RebornCore-5.8.3.jar"},
                {"url": "https://disk.yandex.ru/d/_CgYmn4OYeGnBQ", "file": "servercore-fabric-1.5.2+1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/uI7zlr5Yg-7skQ", "file": "sodium-extra-0.5.9+mc1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/Mft3dmbdbHjhHA", "file": "sodium-fabric-0.5.13+mc1.20.1.jar"},
                {"url": "https://disk.yandex.ru/d/dncEQy1PhTcgrw", "file": "TechReborn-5.8.3.jar"},
                {"url": "https://disk.yandex.ru/d/_c-mQTKC4UB1cw", "file": "Terralith_1.20.x_v2.5.4.jar"},
                {"url": "https://disk.yandex.ru/d/trH1NQ3Hw2QjXQ", "file": "Xaeros_Minimap_25.2.10_Fabric_1.20.jar"},
                {"url": "https://disk.yandex.ru/d/H0dkq2G5XcrZFQ", "file": "moonlight-1.20-2.16.15-fabric.jar"},
                {"url": "https://disk.yandex.ru/d/uXJYqfjy_aedHQ",
                 "file": "immersive_weathering-1.20.1-2.0.5-fabric.jar"},
                {"url": "https://disk.yandex.ru/d/7ebHrjGobc89Og",
                 "file": "travelersbackpack-fabric-1.20.1-9.1.41.jar"},
            ]
        }

    def _load_config(self) -> Dict[str, Any]:
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}")

        return self.default_config.copy()

    def save(self) -> bool:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")
            return False

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def __getitem__(self, key: str):
        return self.data[key]

    def __setitem__(self, key: str, value: Any):
        self.data[key] = value