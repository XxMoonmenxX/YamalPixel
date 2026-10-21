from pathlib import Path
import json
ROOT = Path('C:/Users/Moonmen/MCMod').resolve()
CHANGES = [
('BuildCraft-Fabric-1.20.1/port/src/main/java/buildcraft/core/BCCoreCreativeTabs.java', '.title(Component.translatable("itemGroup.buildcraft.main"))', '.title(Component.translatable("itemGroup.buildcraft.main").append(" - XxMoonmenxX"))'),
('BuildCraft-1.20.1/version-src/1.20.1-forge/src/main/java/buildcraft/core/BCCore.java', '.title(Component.translatable("itemGroup.buildcraft.main"))', '.title(Component.translatable("itemGroup.buildcraft.main").append(" - XxMoonmenxX"))'),
('src/main/java/com/moonmen/resonanceecho/item/ModCreativeTab.java', '.title(Component.translatable("itemGroup.resonanceecho"))', '.title(Component.translatable("itemGroup.resonanceecho").append(" - XxMoonmenxX"))'),
('MeadCraft/src/main/java/ru/yamalpixel/mead/MeadItem.java', 'public void appendHoverText(ItemStack stack,Level level,List<Component> lines,TooltipFlag flag){', 'public void appendHoverText(ItemStack stack,Level level,List<Component> lines,TooltipFlag flag){\n        lines.add(Component.literal("XxMoonmenxX").withStyle(ChatFormatting.DARK_GRAY));'),
('SweetBerryJam/src/main/java/ru/yamalpixel/jam/JamItem.java', 'public void appendHoverText(ItemStack stack,Level level,List<Component> lines,TooltipFlag flag){', 'public void appendHoverText(ItemStack stack,Level level,List<Component> lines,TooltipFlag flag){\n        lines.add(Component.literal("XxMoonmenxX").withStyle(ChatFormatting.DARK_GRAY));')]
def main(write=False):
    plan=[]
    for rel, before, after in CHANGES:
        p=(ROOT/rel).resolve()
        if not p.is_relative_to(ROOT): raise ValueError(p)
        raw=p.read_bytes(); text=raw.decode('utf-8')
        after=after.replace('\n','\r\n' if '\r\n' in text else '\n')
        if after in text: continue
        if text.count(before)!=1: raise ValueError('Expected one fragment: '+str(p))
        plan.append((p,raw,text.replace(before,after,1).encode('utf-8')))
    print(json.dumps({'mode':'write' if write else 'preview','files':[str(p) for p,_,_ in plan]},indent=2))
    if write:
        changed=[]
        try:
            for p,raw,new in plan:
                if p.read_bytes()!=raw: raise RuntimeError('Source changed: '+str(p))
                changed.append((p,raw)); p.write_bytes(new)
        except Exception:
            for p,raw in reversed(changed): p.write_bytes(raw)
            raise
if __name__=='__main__':
    import sys
    main('--write' in sys.argv)

