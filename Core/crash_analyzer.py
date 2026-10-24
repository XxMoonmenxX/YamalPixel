"""Offline explanations of Minecraft failures. Rules describe evidence, not guesses.

Public APIs return plain JSON-compatible dictionaries; no network request, deletion,
mod disabling or executable launch is performed here.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

SOURCES = [
    'https://docs.fabricmc.net/players/troubleshooting/crash-reports',
    'https://docs.oracle.com/en/java/javase/25/troubleshoot/troubleshooting-memory-leaks.html',
    'https://www.glfw.org/docs/latest/group__errors.html',
    'https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-4.html',
]
LIMITATIONS = ('Анализатор объясняет известные признаки из журналов. Без точного сообщения '
               'об ошибке причину установить нельзя; наличие мода в стеке само по себе '
               'не доказывает его вину или конфликт двух модов.')


def _unique(values):
    return list(dict.fromkeys(value for value in values if value))


def _safe(text):
    # Reports may be sent to other people; do not copy launcher credentials.
    from Core.bugreport import redact
    return redact(str(text))


def _redact_data(value):
    if isinstance(value, str):
        return _safe(value)
    if isinstance(value, dict):
        return {str(key): _redact_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_data(item) for item in value]
    return value


def _lines(text, pattern, limit=8):
    rx = re.compile(pattern, re.I)
    return _unique(_safe(line.strip())[:1400] for line in text.splitlines()
                   if rx.search(line) and not re.search(r'\bWARN(?:ING)?\b|/DEBUG\]', line))[:limit]


def _failure_block(text):
    """Prefer the actual crash over unrelated startup warnings/errors."""
    markers = list(re.finditer(r'^.*---- Minecraft Crash Report ----.*$', text, re.M))
    if markers:
        return text[markers[-1].start():]
    markers = list(re.finditer(
        r'^.*(?:A fatal error has been detected by the Java Runtime|'
        r'Error occurred during initialization of VM|'
        r'Incompatible mods found!|Mod resolution encountered an incompatible mod set|'
        r'Some of your mods are incompatible with the game|'
        r'Encountered an unexpected exception|Unreported exception thrown!|'
        r'Unhandled game exception|Exception in thread "(?:main|Render thread)"|'
        r'\[(?:Render thread|main)/FATAL\]).*$', text, re.M | re.I))
    if markers:
        # Dependency wrappers can repeat *after* the precise requirements; keep
        # that block together, without pulling a separate earlier failure in.
        index = markers[-1].start()
        dependency = re.compile(r'incompatible|mod resolution', re.I)
        if dependency.search(markers[-1].group()):
            for previous in reversed(markers[:-1]):
                if index - previous.start() > 20000 or not dependency.search(previous.group()):
                    break
                index = previous.start()
        return text[index:]
    return text[-400000:]


def _fatal_evidence(text):
    text = '\n'.join(line for line in text.splitlines()
                     if not re.search(r'\bWARN(?:ING)?\b|/DEBUG\]', line))
    return bool(re.search(
        r'---- Minecraft Crash Report ----|A fatal error has been detected|'
        r'Error occurred during initialization of VM|Incompatible mods found!|'
        r'Mod resolution encountered an incompatible mod set|Some of your mods are incompatible with the game|'
        r'Reported exception thrown!|Failed to start Minecraft|'
        r'Error:\s*Could not find or load main class|Error:\s*Unable to initialize main class|'
        r'Error:\s*(?:Unrecognized VM option|Unrecognized option:)|'
        r'Unhandled game exception|Encountered an unexpected exception|'
        r'Unreported exception thrown|Exception in thread "(?:main|Render thread)"|'
        r'\[(?:Render thread|main)/FATAL\]|'
        r'Could not (?:reserve enough space|create the Java Virtual Machine)|'
        r'(?:java\.lang\.)?(?:OutOfMemoryError|UnsupportedClassVersionError)\s*:',
        text, re.I))


def map_package_to_mod(package_name, minecraft_dir=None):
    """Map a Java package to a mod id using fabric.mod.json metadata."""
    if not minecraft_dir: return None
    package_name=package_name.rstrip('.').lower()
    try:
        for jar in (Path(minecraft_dir)/'mods').glob('*.jar'):
            with zipfile.ZipFile(jar) as archive:
                if 'fabric.mod.json' not in archive.namelist(): continue
                data=json.loads(archive.read('fabric.mod.json'))
                mod_id=data.get('id'); packages=data.get('provides',[]) or data.get('custom',{}).get('packages',[])
                candidates=list(packages) if isinstance(packages,list) else []
                candidates += [str(data.get('id','')).replace('-','_')]
                if mod_id and any(package_name.startswith(str(p).lower()) for p in candidates if p):
                    return f'{mod_id} (Высокая уверенность)'
    except (OSError, zipfile.BadZipFile, ValueError, TypeError):
        pass
    return None

def _suspects(text, context=None):
    found = []
    found += re.findall(r"\bMod\s+['\"]([^'\"]+)['\"]\s*\(([\w.-]+)\)", text)
    names = [f'{name} ({mod_id})' for name, mod_id in found]
    names += re.findall(r'\bfrom mod\s+([\w.-]+)', text, re.I)
    names += re.findall(r'\bprovided by\s+[\'"]([^\'\"]+)', text, re.I)
    names += re.findall(r'\b(?:Block|Entity|Name|ID):\s*([a-z][a-z0-9_.-]+:[a-z0-9_/.-]+)', text)
    # Package ownership can be ambiguous; only report explicitly named IDs/classes.
    names += re.findall(r'^\s*at\s+([^\s(]+)', text, re.M)[:8]
    for package in re.findall(r'^\s*at\s+([a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)+)', text, re.M):
        mapped=map_package_to_mod(package, (context or {}).get('minecraft_dir'))
        if mapped: names.insert(0,mapped)
    return _unique(names)[:12]


def analyze_text(text, exit_code=None, context=None):
    """Explain a current session's log. ``exit_code`` alone never names a cause.

    ``causes`` entries have id, summary, confidence, evidence; the first entry is
    the primary diagnosis. A clean exit ignores recoverable warnings/exceptions.
    """
    context = context or {}
    text = str(text or '')
    block = _failure_block(text)
    fatal = _fatal_evidence(block)
    crashed = exit_code not in (None, 0) or fatal
    result = dict(category='unknown', title='Причина завершения не определена',
                  summary='В журнале нет достаточно данных для точного объяснения.',
                  confidence='low', crashed=bool(crashed), causes=[], actions=[],
                  evidence=[], suspects=[], limitations=LIMITATIONS,
                  exit_code=exit_code, sources=SOURCES.copy())
    if not crashed:
        disconnected = bool(re.search(r'Disconnected|Connection (?:timed out|reset)|'
                                      r'Failed to (?:connect to|verify username)|'
                                      r'Authentication servers are down|Invalid session|'
                                      r'Outdated (?:client|server)|mismatched mod', block, re.I))
        result.update(category='disconnect' if disconnected else 'normal',
                      title='Соединение с сервером прервано' if disconnected else 'Игра закрылась без признаков краша',
                      summary=('В журнале есть ошибка подключения, но аварийное завершение игры не подтверждено.'
                               if disconnected else 'Процесс завершился штатно; предупреждения в журнале сами по себе не означают краш.'),
                      confidence='high' if exit_code == 0 else 'low')
        if disconnected:
            result['actions'] = ['Проверьте адрес и доступность сервера, интернет и совпадение версий игры и модов с сервером.']
            result['evidence'] = _lines(block, r'disconnect|connection (?:timed out|reset)|invalid session|outdated (?:client|server)|mismatched mod|authentication servers')
        return result

    def add(category, title, summary, pattern, actions, confidence='high', source=None):
        evidence = _lines(block if source is None else source, pattern)
        if evidence:
            result['causes'].append(dict(id=category, summary=summary, confidence=confidence,
                                         evidence=evidence))
            if result['category'] == 'unknown':
                result.update(category=category, title=title, summary=summary,
                              confidence=confidence)
            result['actions'].extend(actions)
            result['evidence'].extend(evidence)

    # Specific root causes before generic exception wrappers and render symptoms.
    java = re.search(r'class file version\s+(\d+)(?:\.\d+)?.*?(?:up to|recognizes class file versions up to)\s+(\d+)', block, re.I | re.S)
    java_detail = ''
    if java:
        needed, actual = (int(value) - 44 for value in java.groups())
        java_detail = f' Моду нужна Java {needed}, а запущена Java {actual}.'
    java_dependencies = _lines(block, r'\brequires\b.*\(java\).*(?:missing|wrong version|but only)')
    if java_dependencies and not java_detail:
        requirement = re.search(r'requires\s+(?:(?:any\s+)?version\s+(?:between\s+)?)?(\d+).*?\(java\)', java_dependencies[0], re.I)
        actual = re.search(r'present:\s*([\d.]+)', java_dependencies[0], re.I)
        if requirement:
            java_detail = f' Загрузчик требует Java {requirement[1]} или подходящую версию из указанного диапазона.'
            if actual:
                java_detail += f' Сейчас используется Java {actual[1].rstrip(".")}.'
    add('java_version', 'Неподходящая версия Java',
        'Игра или мод собраны для другой версии Java.' + java_detail,
        r'UnsupportedClassVersionError|compiled by a more recent version|Unsupported class file major version|\brequires\b.*\(java\).*(?:missing|wrong version|but only)',
        ['Выберите в настройках Java подходящей версии для этой игры и модов; не меняйте Fabric/Forge наугад.'])
    add('jvm_arguments', 'Java не приняла параметры запуска',
        'В параметрах запуска есть неизвестный, устаревший или некорректный аргумент.',
        r'Unrecognized VM option|Unrecognized option:|Invalid (?:maximum|initial) heap size|Invalid (?:thread stack size|flag)|Improperly specified VM option|Initial heap size set to a larger value than the maximum heap size',
        ['Сбросьте дополнительные параметры JVM; проверьте, что начальная память не превышает максимальную.'])
    add('memory_reservation', 'Java не смогла зарезервировать память',
        'Указанный объём памяти недоступен процессу Java ещё до загрузки игры.',
        r'Could not reserve enough space|Could not allocate compressed class space|Could not create the Java Virtual Machine.*memory',
        ['Уменьшите выделенную игре память, закройте лишние программы; для большой сборки используйте 64-битную Java.'])
    add('memory_native', 'Не хватает памяти Windows или ресурсов системы',
        'Java не смогла получить системную память или создать поток. Увеличение памяти игры может ухудшить ситуацию.',
        r'Native memory allocation.*failed|There is insufficient memory for the Java Runtime|unable to create (?:new )?native thread|OutOfMemoryError:\s*(?:Direct buffer memory|Cannot reserve.*direct buffer)|paging file is too small|error=1455|os::commit_memory.*failed|Failed to map memory',
        ['Закройте другие программы, оставьте Windows свободную ОЗУ и проверьте файл подкачки.',
         'Если игре выделена почти вся ОЗУ, уменьшите лимит; при повторении проверьте утечку памяти в модах.'])
    add('memory_metaspace', 'Java исчерпала память классов',
        'Закончилась область памяти, где Java хранит загруженные классы модов.',
        r'OutOfMemoryError:\s*(?:Metaspace|Compressed class space)',
        ['Уберите искусственный лимит MaxMetaspaceSize из параметров JVM; проверьте моды на утечку загрузчиков классов.'])
    add('memory_gc', 'Java тратит всё время на очистку памяти',
        'Память Java почти заполнена, и сборщик мусора не может освободить достаточно места.',
        r'OutOfMemoryError:\s*GC overhead limit exceeded',
        ['Увеличьте память игры, если в системе есть свободная ОЗУ, и уменьшите дальность прорисовки/нагрузку модов.'])
    add('memory_array', 'Мод запросил слишком большой массив',
        'Запрошенный массив превышает ограничение Java; это может быть ошибка мода или повреждённые входные данные.',
        r'OutOfMemoryError:\s*Requested array size exceeds VM limit',
        ['Найдите мод в цепочке исключений и проверьте его обновления/данные; одно увеличение ОЗУ не снимает ограничение массива.'])
    add('memory_heap', 'Игре не хватило выделенной памяти Java',
        'Закончилась память Java для объектов Minecraft и модов.',
        r'OutOfMemoryError:\s*(?:Java heap space|Java heap memory)|OutOfMemoryError\s*$',
        ['Увеличьте память игры в настройках, оставив ОЗУ для Windows; уменьшите дальность прорисовки и тяжёлые эффекты.',
         'Если память быстро заполняется снова, проверьте обновления модов и возможную утечку.'])
    add('disk_full', 'На диске закончилось место',
        'Игра не смогла записать или распаковать данные из-за нехватки места.',
        r'No space left on device|There is not enough space on the disk|disk (?:is )?full|Недостаточно места на диске',
        ['Освободите место на диске с игрой и во временной папке; сохраните резервную копию мира.'])
    add('permissions', 'Игра не может прочитать или изменить файл',
        'Операционная система запретила доступ к файлу или файл занят другой программой.',
        r'AccessDeniedException|Permission denied|Access is denied|Отказано в доступе|being used by another process',
        ['Закройте второй экземпляр игры и программы, занявшие файл; проверьте права папки и журнал антивируса.'])
    add('duplicate_mod', 'Установлены дубликаты модов',
        'Загрузчик обнаружил несколько файлов одного мода или повторяющийся идентификатор.',
        r'Duplicate (?:mods?|mod id|versions)|Found duplicate mods|Mod ID.*is duplicated|DuplicateModsFoundException',
        ['Оставьте одну подходящую версию каждого указанного мода в папке mods; лишние JAR переместите в резервную папку.'])
    dependency_source = block
    if java_dependencies:
        dependency_source = '\n'.join(line for line in block.splitlines() if not re.search(
            r'\brequires\b.*\(java\)|Incompatible mods found!|incompatible mod set|Some of your mods are incompatible', line, re.I))
    add('mod_dependency', 'Не хватает зависимости или не совпадают версии модов',
        'Загрузчик прямо указал несовместимые версии или недостающий обязательный мод. Точные требования приведены ниже.',
        r"\brequires\b.*(?:missing|wrong version|but only)|\bdepends\b.*(?:missing|version)|Missing (?:or unsupported )?(?:mandatory )?dependencies|MissingModsException|requires.*(?:we have|you have|Currently)|ModLoadingException.*requires|fml\.modloading\.missingdependency|Requested by:.*Expected range:.*Actual version:|\bneeds\b.*not installed|is incompatible with|Found incompatible mods|Incompatible mods found!|incompatible mod set|Some of your mods are incompatible",
        ['Установите указанные обязательные зависимости и подберите версии именно для выбранных Minecraft и загрузчика.',
         'Если загрузчик назвал два несовместимых мода, обновите их совместно или уберите один из них.'],
        source=dependency_source)
    dependency_details = []
    for line in _lines(dependency_source, r"\bMod\s+['\"].*(?:requires|is incompatible with)", limit=8):
        mods = re.findall(r"(?:[Mm]od\s+)?['\"]([^'\"]+)['\"]\s*\(([\w.-]+)\)", line)
        if len(mods) >= 2:
            first, second = (f'{name} ({mod_id})' for name, mod_id in mods[:2])
            if 'incompatible with' in line:
                dependency_details.append(f'{first} несовместим с {second}: это прямо указал загрузчик.')
            elif 'missing' in line:
                dependency_details.append(f'Для {first} нужен {second}, который не установлен.')
            elif 'wrong version' in line:
                dependency_details.append(f'Для {first} установлена неподходящая версия {second}; требования есть в строке журнала.')
        elif len(mods) == 1 and 'missing' in line:
            dependency = re.search(r'\bof\s+([\w.-]+),\s*which is missing', line)
            if dependency:
                dependency_details.append(f'Для {mods[0][0]} ({mods[0][1]}) нужен отсутствующий мод {dependency[1]}.')
    if dependency_details:
        for cause in result['causes']:
            if cause['id'] == 'mod_dependency':
                cause['summary'] = ' '.join(dependency_details)
                if result['category'] == 'mod_dependency':
                    result['summary'] = cause['summary']
        result['actions'] = dependency_details + result['actions']
    missing_ids = []
    for pattern in (
        r"requires\s+(?:version\s+[^\s]+\s+of\s+)?['\"]?[^('\"]+['\"]?\s*\(([^)]+)\).*?missing",
        r"Mod\s+ID:\s*['\"]([^'\"]+)['\"]",
        r"missing[^\n]*?\(([-\w.]+)\)",
    ):
        missing_ids.extend(re.findall(pattern, dependency_source, re.I))
    missing_ids.extend(re.findall(r"of\s+([\w-]+),\s+which is missing", dependency_source, re.I))
    result['missing_dependency_ids'] = _unique([x.strip() for x in missing_ids if re.fullmatch(r'[a-z0-9_.-]+', x.strip(), re.I)])
    add('wrong_environment', 'Мод запущен не на той стороне или загрузчике',
        'Код мода обращается к клиентским классам на сервере либо не подходит выбранному окружению.',
        r'Attempted to load class.*for invalid dist|Cannot load class.*in environment type SERVER|client-only mod.*server|requires.*(?:forge|neoforge|fabricloader).*missing|not a valid mod file|is a (?:Fabric|Forge|NeoForge) mod.*cannot be loaded',
        ['Проверьте, что JAR предназначен для вашего Fabric/Forge/NeoForge и нужной стороны: клиент или сервер.'])
    add('archive_corrupt', 'Повреждён JAR или архив',
        'Java не смогла прочитать архив мода или библиотеки.',
        r'ZipException|zip END header not found|invalid (?:LOC|CEN) header|error in opening zip file|Invalid or corrupt jarfile|invalid entry (?:size|CRC)|zip file is empty',
        ['По имени файла в сообщении определите повреждённый JAR и скачайте его заново; сохраните собственные моды отдельно.'])
    add('config_corrupt', 'Ошибка в конфигурации или JSON',
        'Файл настроек или метаданных имеет неверный формат либо содержит неподдерживаемое значение.',
        r'MalformedJsonException|JsonParseException|JsonSyntaxException|ParsingException|Failed to (?:parse|load).*config|Error reading fabric\.mod\.json|TomlParsingException|Invalid (?:toml|json)',
        ['Сделайте копию указанного файла и исправьте ошибку формата; для настроек мода можно временно переименовать только его конфиг.'])
    add('registry', 'Набор модов или данные мира не совпадают',
        'Игра не смогла сопоставить зарегистрированные блоки, предметы или данные пакетов.',
        r'Failed to load registries|Registry remapping failed|Unbound values in registry|Unbound registry entries|Missing registry data|Errors in currently selected datapacks|Failed to load datapacks|Unknown registry key|Missing required datapack',
        ['Проверьте версии модов и датапаки; для сервера сравните сборки клиента и сервера.',
         'Перед изменением состава модов сделайте резервную копию мира; не удаляйте блоки и данные вслепую.'])
    add('graphics_opengl', 'Не удалось создать графическое окно OpenGL',
        'Видеодрайвер или выбранный графический адаптер не предоставил нужный игре OpenGL-контекст.',
        r'GLFW error (?:65542|65543|65545)|WGL:.*(?:OpenGL|pixel format)|GLX:.*(?:context|FBConfig)|Failed to create.*(?:window|OpenGL context)|The driver does not appear to support OpenGL|Pixel format not accelerated|OpenGL.*not supported',
        ['Установите драйвер видеокарты с сайта производителя и выберите дискретную видеокарту для Java.',
         'Проверьте поддержку OpenGL вашей видеокартой; удалённый рабочий стол и виртуальная машина могут ограничивать графику.'])
    add('native_library', 'Не удалось загрузить системную библиотеку игры',
        'Java не может найти или загрузить DLL/нативную библиотеку либо её архитектура не совпадает с Java.',
        r'UnsatisfiedLinkError|Can.t load (?:AMD 64|IA 32)-bit|Can.t load.*\.dll|not a valid Win32 application|no lwjgl.*in java\.library\.path|Failed to locate library:|Failed to load.*lwjgl',
        ['Используйте Java той же архитектуры, что и система; повторно установите библиотеки игры и проверьте карантин антивируса.'])
    add('main_class', 'Java не смогла запустить главный класс игры',
        'Не найден или не загружается стартовый класс Minecraft/загрузчика; возможны неполные библиотеки или неправильная команда запуска.',
        r'Could not find or load main class|Unable to initialize main class',
        ['Проверьте установку версии игры и загрузчика, наличие библиотек и правильность пути запуска.'], 'medium')
    add('shader', 'Ошибка загрузки шейдера',
        'При компиляции или связывании шейдера произошла ошибка. По логу нельзя автоматически объявить виновным видеодрайвер.',
        r'ShaderCompileException|Shader compilation failed|Failed to compile.*shader|Could not compile.*shader|Failed to link.*shader',
        ['Временно отключите шейдерпак и проверьте совместимость его версии с Iris/OptiFine и видеокартой.'], 'medium')
    add('mixin', 'Мод не смог применить изменение к коду игры',
        'Mixin не нашёл ожидаемый код или обнаружил несовместимое изменение; часто это неподходящая версия мода или конфликт.',
        r'MixinApplyError|MixinTransformerError|InvalidMixinException|InjectionError|InvalidInjectionException|Critical injection failure|Mixin apply .*failed|@Mixin target.*not found',
        ['Проверьте мод после «from mod» и версии его зависимостей; используйте сборку для вашего Minecraft и загрузчика.',
         'Если второй мод явно не назван загрузчиком, точную пару нужно проверять отключением подозреваемых модов по одному.'], 'medium')
    add('api_mismatch', 'Мод обращается к отсутствующему коду',
        'Не найден класс, метод или поле. Обычно установлен мод/зависимость другой версии, но иногда файл отсутствует.',
        r'NoSuchMethodError|NoSuchFieldError|AbstractMethodError|NoClassDefFoundError|ClassNotFoundException|IncompatibleClassChangeError',
        ['Сверьте версии игры, загрузчика и зависимостей указанного мода; проверьте наличие нужной библиотеки.'], 'medium')
    add('stack_overflow', 'Код игры или мода зациклился',
        'Цепочка вызовов переполнила стек Java, часто из-за рекурсии в моде или циклических данных.',
        r'StackOverflowError',
        ['Посмотрите повторяющиеся вызовы в стеке, обновите связанный мод; сохраните мир перед изменением данных.'], 'medium')

    # A rendering/ticking report is useful even if a more specific OOM was found.
    add('world_render', 'Сбой при отрисовке блока или сущности',
        'Игра упала при рисовании объекта мира. В отчёте ниже указаны объект и место, если Minecraft их сохранил.',
        r'Description:\s*(?:Rendering (?:Block Entity|entity|screen|overlay)|Tesselating block|Tessellating block)|Block entity being rendered|Entity being rendered|Exception (?:tessellating|rendering)',
        ['Проверьте обновления указанного мода и графических модов; временно отключите шейдеры для проверки.',
         'Если вылет привязан к месту, перед изменением проблемного объекта попросите администратора сделать резервную копию мира.'], 'medium')
    add('world_tick', 'Сбой при обработке объекта или мира',
        'Игра упала при обновлении сущности, блока или мира; это может повторяться при загрузке того же участка.',
        r'Description:\s*(?:Ticking (?:entity|block entity|world)|Exception (?:ticking|in server tick loop))|Entity being ticked|Block entity being ticked',
        ['Сохраните резервную копию мира и проверьте мод объекта, его зависимости и обновления; не удаляйте мир.'], 'medium')
    add('native_crash', 'Аварийно завершилась Java или системная библиотека',
        'Процесс упал в нативном коде. DLL в «Problematic frame» показывает место сбоя, но не доказывает первопричину.',
        r'A fatal error has been detected by the Java Runtime|EXCEPTION_ACCESS_VIOLATION|SIGSEGV|SIGBUS|Problematic frame:|EXCEPTION_ILLEGAL_INSTRUCTION',
        ['Откройте hs_err_pid*.log и строку Problematic frame; обновите подходящую Java и драйвер указанного устройства.',
         'Если в стеке видеодрайвер, проверьте запуск без шейдеров/графических модов; код выхода сам по себе не определяет причину.'], 'medium')
    add('download_network', 'Не удалось получить необходимые данные по сети',
        'Запуск прервался на сетевом запросе; адрес и точная ошибка приведены ниже.',
        r'UnknownHostException|ConnectTimeoutException|SSLHandshakeException|PKIX path building failed|Failed to download|Connection refused|Network is unreachable',
        ['Проверьте доступность адреса из ошибки, прокси и время Windows; SSL-проверку не отключайте.'], 'medium')
    add('exception', 'Ошибка в коде игры или мода',
        'Зафиксировано необработанное исключение. По одному названию исключения точную несовместимую пару определить нельзя.',
        r'NullPointerException|IllegalStateException|ClassCastException|IllegalArgumentException|IndexOutOfBoundsException|ArithmeticException|ConcurrentModificationException|ExceptionInInitializerError',
        ['Сверьте первые вызовы после исключения и цепочку «Caused by»; передайте полный Bugreport.txt автору сборки.'], 'low')

    details = _lines(block, r'^\s*(?:Block(?: entity)?:|Entity Type:|Entity ID:|Name:\s*[a-z][a-z0-9_.-]+:|Block location:|Exact location:|#?\s*Problematic frame:|#?\s*[CVJ]\s+\[[^\]]+\.(?:dll|so))')
    result['evidence'] = _unique(result['evidence'] + details)[:24]
    result['actions'] = _unique(result['actions'])[:8]
    result['suspects'] = _suspects(block, context)
    if result['category'] in ('world_render', 'world_tick'):
        obj = re.search(r'\b(?:Name|Block|Entity Type):\s*([a-z][a-z0-9_.-]+:[a-z0-9_/.-]+)', block)
        location = re.search(r'(?:Block location:.*?World:|Exact location:)\s*\(([^)]+)\)', block)
        if obj:
            result['summary'] += f' Объект: {obj[1]}.'
        if location:
            result['summary'] += f' Координаты: ({location[1]}).'
    if result['category'] == 'unknown':
        result.update(title='Игра завершилась аварийно, причина не установлена',
                      summary=f'Код завершения: {exit_code}. Подходящей подтверждённой причины в доступных журналах нет.',
                      actions=['Откройте полный Bugreport.txt и сохраните свежие latest.log, crash-reports и hs_err_pid*.log.',
                               'Если процесс завершён вручную, антивирусом или Windows, Java может не успеть записать исключение.'])
        result['evidence'] = _lines(block, r'Caused by:|Exception|Error|FATAL|exit code')[-8:]
    return result


def _started_at(context):
    value = context.get('started') or context.get('started_at')
    if isinstance(value, (int, float)):
        return float(value)
    if value:
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00')).timestamp()
        except (ValueError, TypeError):
            pass
    return None


def _read_tail(path, maximum=2_000_000, preserve_head=False):
    with path.open('rb') as source:
        size = path.stat().st_size
        if preserve_head and size > maximum:
            head = source.read(maximum // 2)
            source.seek(size - maximum // 2)
            return (head + b'\n[... middle omitted; complete file in Bugreport.txt ...]\n' + source.read()).decode('utf-8-sig', errors='replace')
        source.seek(max(0, path.stat().st_size - maximum))
        return source.read(maximum).decode('utf-8-sig', errors='replace')


def analyze_session(minecraft_dir, context=None, exit_code=None):
    """Read only current-session game logs; never diagnose an old crash as new.

    Without a start timestamp use only the supplied Java console or last_session
    metadata. If neither exists, return an explicit unknown result, not an old log.
    """
    game = Path(minecraft_dir)
    context = dict(context or {})
    if not context:
        try:
            loaded = json.loads((game / 'logs' / 'launch-session.json').read_text(encoding='utf-8'))
            context = loaded if isinstance(loaded, dict) else {}
        except (OSError, ValueError, TypeError):
            context = {}
    if exit_code is None:
        exit_code = context.get('exit_code')
    started = _started_at(context)
    console = Path(context['java_console']) if context.get('java_console') else None
    paths = []
    if console is not None:
        paths.append(console)
    paths += [game / 'logs' / 'latest.log', game / 'logs' / 'debug.log']
    paths += sorted((game / 'crash-reports').glob('crash-*.txt'))
    paths += sorted(game.glob('hs_err_pid*.log'))
    paths += sorted((game / 'logs').glob('hs_err_pid*.log'))
    files, ignored, read_errors = [], 0, []
    snapshots = {os.path.normcase(os.path.abspath(key)): value
                 for key, value in (context.get('log_snapshots') or {}).items()}
    for path in dict.fromkeys(paths):
        try:
            stat = path.stat()
            if not path.is_file():
                continue
            if started is None and path != console:
                ignored += 1
                continue
            if started is not None and stat.st_mtime < started:
                ignored += 1
                continue
            old = snapshots.get(os.path.normcase(os.path.abspath(path)))
            if isinstance(old, dict) and old.get('mtime_ns') == stat.st_mtime_ns and old.get('size') == stat.st_size:
                ignored += 1
                continue
            if path.name.startswith('hs_err_pid') and context.get('pid'):
                if path.stem != f'hs_err_pid{context["pid"]}':
                    ignored += 1
                    continue
            contents = _read_tail(path, preserve_head=path.parent.name == 'crash-reports' or path.name.startswith('hs_err_pid'))
            # A fresh crash report is the most authoritative description. Keep it
            # last so its causal stack wins over recoverable startup errors.
            priority = 2 if path.parent.name == 'crash-reports' else 3 if path.name.startswith('hs_err_pid') else 1 if path == console else 0
            files.append((priority, stat.st_mtime, path, contents))
        except FileNotFoundError:
            continue
        except OSError as exc:
            read_errors.append(_safe(f'{path}: {exc}'))
    files.sort(key=lambda value: (value[0], value[1]))
    text = '\n\n'.join(f'=== {path.name} ===\n{contents}' for _, _, path, contents in files)
    result = analyze_text(text, exit_code=exit_code, context=context)
    result['log_files'] = [str(path) for _, _, path, _ in files]
    result['ignored_logs'] = ignored
    result['read_errors'] = read_errors
    result['session'] = {key: _redact_data(context[key]) for key in (
        'started', 'pid', 'selected_version', 'minecraft', 'minecraft_version', 'minecraft_dir', 'java_console') if key in context}
    if not files and result['crashed']:
        result['summary'] += ' Свежих журналов этого запуска не найдено.'
    return result


def write_analysis(analysis, minecraft_dir):
    """Atomically write a readable report plus machine-readable local JSON."""
    game = Path(minecraft_dir)
    logs = game / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    report = game / 'CrashAnalysis.txt'
    text = [analysis.get('title', ''), analysis.get('summary', ''),
            f'Уверенность: {analysis.get("confidence", "low")}',
            f'Код завершения: {analysis.get("exit_code")}', '', 'Что делать:']
    text += [f'{index}. {action}' for index, action in enumerate(analysis.get('actions', []), 1)]
    text += ['', 'Признаки из журнала:'] + analysis.get('evidence', [])
    text += ['', 'Упомянутые моды/классы (не доказательство вины):'] + analysis.get('suspects', [])
    text += ['', 'Проверенные журналы:'] + analysis.get('log_files', [])
    text += ['', analysis.get('limitations', LIMITATIONS), '', 'Справочные источники:'] + SOURCES
    outputs = [(report, _safe('\n'.join(text)) + '\n'),
               (logs / 'crash-analysis.json', json.dumps(_redact_data(analysis), ensure_ascii=False, indent=2))]
    for target, contents in outputs:
        fd, temporary = tempfile.mkstemp(prefix=target.stem + '-', suffix='.tmp', dir=target.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(contents)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return str(report)


if __name__ == '__main__':
    import argparse
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Explain Minecraft crash logs without network access')
    parser.add_argument('--log', type=Path, help='Analyze an explicitly selected log, including an older crash report')
    parser.add_argument('--minecraft-dir', type=Path, help='Analyze the last launcher session in this directory')
    parser.add_argument('--exit-code', type=int)
    args = parser.parse_args()
    if args.log:
        analysis = analyze_text(_read_tail(args.log, preserve_head=True), args.exit_code)
        analysis['log_files'] = [str(args.log)]
    elif args.minecraft_dir:
        analysis = analyze_session(args.minecraft_dir, exit_code=args.exit_code)
    else:
        parser.error('Specify --log or --minecraft-dir')
    print(json.dumps(_redact_data(analysis), ensure_ascii=False, indent=2))
