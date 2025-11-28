CURRENT_VERSION = "0.8.0"

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


fabric_supported_versions = [
    "YamalPixel",
    "Minecraft 1.14.4 + Fabric",
    "Minecraft 1.15.2 + Fabric",
    "Minecraft 1.16.5 + Fabric",
    "Minecraft 1.17.1 + Fabric",
    "Minecraft 1.18.2 + Fabric",
    "Minecraft 1.19.2 + Fabric",
    "Minecraft 1.20.1 + Fabric",
    "Minecraft 1.20.2 + Fabric",
    "Minecraft 1.20.3 + Fabric",
    "Minecraft 1.20.4 + Fabric",
    "Minecraft 1.20.5 + Fabric",
    "Minecraft 1.20.6 + Fabric",
    "Minecraft 1.21 + Fabric",
    "Minecraft 1.21.1 + Fabric",
    "Minecraft 1.21.2 + Fabric",
    "Minecraft 1.21.3 + Fabric",
    "Minecraft 1.21.4 + Fabric",
]

quilt_supported_versions = [
    "Minecraft 1.14.4 + Quilt",
    "Minecraft 1.15.2 + Quilt",
    "Minecraft 1.16.5 + Quilt",
    "Minecraft 1.17.1 + Quilt",
    "Minecraft 1.18.2 + Quilt",
    "Minecraft 1.19.2 + Quilt",
    "Minecraft 1.20.1 + Quilt",
    "Minecraft 1.20.2 + Quilt",
    "Minecraft 1.20.3 + Quilt",
    "Minecraft 1.20.4 + Quilt",
    "Minecraft 1.20.5 + Quilt",
    "Minecraft 1.20.6 + Quilt",
    "Minecraft 1.21 + Quilt",
    "Minecraft 1.21.1 + Quilt",
    "Minecraft 1.21.2 + Quilt",
    "Minecraft 1.21.3 + Quilt",
    "Minecraft 1.21.4 + Quilt",
]

neoforge_supported_versions = [
    "Minecraft 1.20.2 + NeoForge",
    "Minecraft 1.20.3 + NeoForge",
    "Minecraft 1.20.4 + NeoForge",
    "Minecraft 1.20.5 + NeoForge",
    "Minecraft 1.20.6 + NeoForge",
    "Minecraft 1.21 + NeoForge",
    "Minecraft 1.21.1 + NeoForge",
    "Minecraft 1.21.2 + NeoForge",
    "Minecraft 1.21.3 + NeoForge",
    "Minecraft 1.21.4 + NeoForge",
]

forge_supported_versions = [
    "Minecraft 1.12.2 + Forge",
    "Minecraft 1.14.4 + Forge",
    "Minecraft 1.15.2 + Forge",
    "Minecraft 1.16.5 + Forge",
    "Minecraft 1.17.1 + Forge",
    "Minecraft 1.18.2 + Forge",
    "Minecraft 1.19.2 + Forge",
    "Minecraft 1.20.1 + Forge",
    "Minecraft 1.20.2 + Forge",
    "Minecraft 1.20.4 + Forge",
    "Minecraft 1.20.6 + Forge",
    "Minecraft 1.21 + Forge",
    "Minecraft 1.21.1 + Forge",
    "Minecraft 1.21.2 + Forge",
    "Minecraft 1.21.3 + Forge",
    "Minecraft 1.21.4 + Forge",
]

versions = [
    "YamalPixel",

    "Minecraft 1.12.2",
    "Minecraft 1.12.2 + Fabric",
    "Minecraft 1.12.2 + Quilt",
    "Minecraft 1.12.2 + Forge",

    "Minecraft 1.14.4",
    "Minecraft 1.14.4 + Fabric",
    "Minecraft 1.14.4 + Quilt",
    "Minecraft 1.14.4 + Forge",

    "Minecraft 1.15.2",
    "Minecraft 1.15.2 + Fabric",
    "Minecraft 1.15.2 + Quilt",
    "Minecraft 1.15.2 + Forge",

    "Minecraft 1.16.5",
    "Minecraft 1.16.5 + Fabric",
    "Minecraft 1.16.5 + Quilt",
    "Minecraft 1.16.5 + Forge",

    "Minecraft 1.17.1",
    "Minecraft 1.17.1 + Fabric",
    "Minecraft 1.17.1 + Quilt",
    "Minecraft 1.17.1 + Forge",

    "Minecraft 1.18.2",
    "Minecraft 1.18.2 + Fabric",
    "Minecraft 1.18.2 + Quilt",
    "Minecraft 1.18.2 + Forge",

    "Minecraft 1.19.2",
    "Minecraft 1.19.2 + Fabric",
    "Minecraft 1.19.2 + Quilt",
    "Minecraft 1.19.2 + Forge",

    "Minecraft 1.20.1",
    "Minecraft 1.20.1 + Fabric",
    "Minecraft 1.20.1 + Quilt",
    "Minecraft 1.20.1 + Forge",
    "Minecraft 1.20.1 + NeoForge",

    "Minecraft 1.20.2",
    "Minecraft 1.20.2 + Fabric",
    "Minecraft 1.20.2 + Quilt",
    "Minecraft 1.20.2 + Forge",
    "Minecraft 1.20.2 + NeoForge",

    "Minecraft 1.20.4",
    "Minecraft 1.20.4 + Forge",

    "Minecraft 1.20.6",
    "Minecraft 1.20.6 + Forge",

    "Minecraft 1.21",
    "Minecraft 1.21 + Fabric",
    "Minecraft 1.21 + Quilt",
    "Minecraft 1.21 + Forge",
    "Minecraft 1.21 + NeoForge",

    "Minecraft 1.21.1",
    "Minecraft 1.21.1 + Fabric",
    "Minecraft 1.21.1 + Quilt",
    "Minecraft 1.21.1 + Forge",
    "Minecraft 1.21.1 + NeoForge",

    "Minecraft 1.21.2",
    "Minecraft 1.21.2 + Fabric",
    "Minecraft 1.21.2 + Quilt",
    "Minecraft 1.21.2 + Forge",
    "Minecraft 1.21.2 + NeoForge",

    "Minecraft 1.21.3",
    "Minecraft 1.21.3 + Fabric",
    "Minecraft 1.21.3 + Quilt",
    "Minecraft 1.21.3 + Forge",
    "Minecraft 1.21.3 + NeoForge",

    "Minecraft 1.21.4",
    "Minecraft 1.21.4 + Fabric",
    "Minecraft 1.21.4 + Quilt",
    "Minecraft 1.21.4 + Forge",
    "Minecraft 1.21.4 + NeoForge"
]

all_versions = [
    "1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2",
    "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4",
    "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
]