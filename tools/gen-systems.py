#!/usr/bin/env python3
"""Give every system Batocera lists a folder in this theme.

    gen-systems.py /path/to/es_systems.cfg [--force]

For each <system> whose <theme> folder is missing here, writes
    <theme>/theme.xml           name, maker/year, blurb and the system's colour
    <theme>/logo{,2,3,4}.png    text wordmarks (tools/mklogo.py, Fira Sans)
plus the automatic collections ES builds (auto-allgames, auto-wheel, ...).
Folders that already exist are left alone unless --force. Hand-written blurbs
and colours live in CURATED; everything else gets a factual one-liner built
from es_systems.cfg and a colour picked by hardware type, so nothing renders
blank or white-on-white again. Re-run after a Batocera update to pick up new
systems.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mklogo  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# theme folder -> (big name, small label, colour, gradient end or None, blurb or None)
CURATED = {
    "pygame": ("Pygame", "Python games and tools", "8B5CF6", "4C3399",
               "Games and tools written in Python with the Pygame library run here, straight from this box. "
               "RomM-o-Cera, the controller-driven RomM client that fills the other systems with games, "
               "box art and manuals, lives in this list."),
    "screenshots": ("Screenshots", "Batocera", "4A4F5A", None,
                    "Every screenshot and recording you take with the hotkey ends up here. Open one to look "
                    "at it full screen; videos play back in the built-in viewer."),
    "steam": ("Steam", "Valve", "1B2838", "66C0F4",
              "Steam games installed through the Flatpak Steam client appear here as shortcuts. Launching one "
              "starts Steam in Big Picture mode with the controller already set up."),
    "flatpak": ("Flatpak", "Linux apps", "4A86CF", None,
                "Desktop applications installed from Flathub. Batocera lists each installed Flatpak so it can be "
                "started from the controller like a game."),
    "windows_installers": ("Windows Installers", "Wine", "0079D7", None,
                           "Windows setup programs dropped here are run through Wine. Once installed, the game "
                           "shows up in the Windows list."),
    "dos": ("MS-DOS", "Microsoft, 1981", "9B2685", None,
            "MS-DOS was the operating system of IBM PC compatibles through the 1980s and early 1990s, and the home "
            "of thousands of games from Sierra, LucasArts, id Software, Apogee and Origin. Batocera runs them "
            "with DOSBox."),
    "fbneo": ("FinalBurn Neo", "Arcade", "F05A28", "B5361B",
              "FinalBurn Neo is an arcade emulator focused on accuracy and speed for Capcom CPS-1/2/3, Neo Geo, "
              "Sega System 16 and hundreds of other boards, with its own well-curated ROM set."),
    "psvita": ("PlayStation Vita", "Sony, 2011", "00439B", None,
               "The PlayStation Vita is Sony's second handheld, with a 5-inch OLED screen, twin analog sticks and "
               "a rear touch pad. Batocera runs it with Vita3K."),
    "ps4": ("PlayStation 4", "Sony, 2013", "003791", None,
            "The PlayStation 4 is Sony's eighth-generation home console. Batocera runs a growing set of titles "
            "with shadPS4."),
    "moonlight": ("Moonlight", "Game streaming", "7B2CBF", None,
                  "Moonlight streams games from a PC running Sunshine or GeForce Experience over the network, "
                  "so the box plays whatever the desktop can run."),
    "library": ("Library", "Documents and media", "6B6B6B", None,
                "PDFs, comics and videos placed in the library folder can be read or watched from the couch."),
    "lowresnx": ("LowRes NX", "Fantasy console", "F2A900", None,
                 "LowRes NX is a fantasy console with an 8-bit look, programmed in BASIC. Its games come as "
                 "small .nx files written by its community."),
    "pico8": ("PICO-8", "Lexaloffle", "FF77A8", "7E2553",
              "PICO-8 is a fantasy console for making, sharing and playing tiny games with a 128x128 display "
              "and a 16-colour palette. Cartridges are PNG images of the game."),
    "tic80": ("TIC-80", "Fantasy computer", "29ADFF", None,
              "TIC-80 is a free fantasy computer for making, playing and sharing tiny games with built-in "
              "code, sprite, map and sound editors."),
    "wasm4": ("WASM-4", "Fantasy console", "E0F8CF", "306850",
              "WASM-4 is a low-resolution fantasy console whose cartridges are small WebAssembly programs, "
              "written in any language that compiles to it."),
    "vectrex": ("Vectrex", "GCE / Milton Bradley, 1982", "2E5A88", None,
                "The Vectrex is the only home console with a built-in vector display: a 9-inch monitor "
                "drawing crisp lines straight from the beam, with colour supplied by plastic overlays."),
    "atari800": ("Atari 8-bit", "Atari, 1979", "6187E5", None,
                 "The Atari 400 and 800 and their XL/XE successors are the home computers built around the "
                 "custom chips that later powered the Atari 5200."),
    "atarist": ("Atari ST", "Atari, 1985", "3F6FB4", None,
                "The Atari ST is a 16-bit home computer with a Motorola 68000, a GUI from day one and MIDI ports "
                "that made it a studio fixture."),
    "jaguar": ("Jaguar", "Atari, 1993", "FFD100", "C79E00",
               "The Atari Jaguar was marketed as the first 64-bit console and was Atari's last home system."),
    "lynx": ("Lynx", "Atari, 1989", "FFCC00", "C09600",
             "The Atari Lynx is the first handheld with a colour LCD, designed by Epyx and sold by Atari."),
    "gamecube": ("GameCube", "Nintendo, 2001", "5B6297", "8B94C2",
                 "The GameCube is Nintendo's sixth-generation home console and the first to use optical discs."),
    "megacd": ("Mega-CD", "Sega, 1991", "30A4EE", None,
               "The Mega-CD (Sega CD in North America) added a CD-ROM drive, a faster CPU and scaling and "
               "rotation hardware to the Mega Drive."),
    "pcenginecd": ("PC Engine CD", "NEC, 1988", "FF6427", None,
                   "The PC Engine CD-ROM² was the first CD add-on for a home console, bringing redbook audio and "
                   "far larger games to NEC's 8-bit machine."),
    "wswan": ("WonderSwan", "Bandai, 1999", "5A5A5A", None,
              "The WonderSwan is a Japanese handheld designed by Gunpei Yokoi's Koto, playable upright or "
              "sideways thanks to two sets of d-pad buttons."),
    "wswanc": ("WonderSwan Color", "Bandai, 2000", "CF0017", None,
               "The WonderSwan Color added a colour screen to Bandai's handheld and kept backwards "
               "compatibility with the original."),
    "auto-allgames": ("All Games", "Game Collections", "2B2D3A", None,
                      "Everything in every system, in one list."),
    "auto-wheel": ("Wheel Games", "Game Collections", "2B2D3A", None,
                   "Games that know how to use a steering wheel."),
    "auto-spinner": ("Spinner Games", "Game Collections", "2B2D3A", None,
                     "Arcade games built for a spinner control."),
    "auto-trackball": ("Trackball Games", "Game Collections", "2B2D3A", None,
                       "Arcade games built for a trackball."),
}

# colour by hardware type for systems not in CURATED (muted, readable under white text)
BY_HARDWARE = {
    "console": "2B4B96", "handheld": "1E8A6A", "computer": "2F6F8F", "arcade": "B5361B",
    "port": "6B4284", "engine": "6B4284", "library": "6B6B6B", "system": "4A4F5A", "virtual": "7B2CBF",
}
HW_WORD = {
    "console": "home console", "handheld": "handheld", "computer": "home computer", "arcade": "arcade system",
    "port": "game port", "engine": "game engine", "library": "software library", "system": "Batocera tool",
    "virtual": "fantasy console",
}

AUTO = {  # collections ES builds itself: (fullname, blurb)
    "auto-allgames": "All Games", "auto-wheel": "Wheel Games", "auto-spinner": "Spinner Games",
    "auto-trackball": "Trackball Games",
}

TEMPLATE = """<theme>

    <formatVersion>7</formatVersion>
    <include>./../theme.xml</include>

	<!-- generated by tools/gen-systems.py (CleanShelf) -->

	<view name="system">

		<text name="systemName" extra="true">
			<text>{name}</text>
			<pos>0.03 0.025</pos>
			<size>0.42 0.3</size>
			<backgroundColor>22222200</backgroundColor>
			<fontPath>./../_inc/fonts/FiraSans-Black.ttf</fontPath>
			<fontSize>{namesize}</fontSize>
			<lineSpacing>0.69</lineSpacing>
			<alignment>left</alignment>
		</text>

		<text name="systemYear" extra="true">
			<text>{label}</text>
			<pos>0.03 0.33</pos>
			<backgroundColor>22222200</backgroundColor>
			<fontPath>./../_inc/fonts/FiraSans-Bold.ttf</fontPath>
			<fontSize>0.035</fontSize>
			<lineSpacing>0.69</lineSpacing>
			<alignment>left</alignment>
		</text>

		<text name="systemtxt" extra="true">
			<text>{blurb}</text>
			<pos>0.03 0.39</pos>
			<size>0.42 0.3</size>
			<backgroundColor>22222200</backgroundColor>
			<fontPath>./../_inc/fonts/FiraSans-Regular.ttf</fontPath>
			<fontSize>0.025</fontSize>
			<lineSpacing>0.89</lineSpacing>
			<alignment>left</alignment>
		</text>

		<image name="background_art" extra="true">
			<color>{color}</color>
			<colorEnd>{colorend}</colorEnd>
		</image>

	</view>

	<view name="detailed">

		<image name="logo">
			<path>./logo2.png</path>
			<pos>0.92 0.048</pos>
			<maxSize>0.1 0.045</maxSize>
			<origin>0.5 0.5</origin>
		</image>

		<image name="gamelistbg" extra="true">
			<color>{color}</color>
			<colorEnd>{colorend}</colorEnd>
		</image>

		<image name="syscolorbar" extra="true">
			<color>{color}</color>
		</image>

	</view>

	<view name="grid">

		<image name="logo">
			<path>./logo2.png</path>
			<pos>0.92 0.048</pos>
			<maxSize>0.1 0.045</maxSize>
			<origin>0.5 0.5</origin>
		</image>

		<image name="gamelistbg" extra="true">
			<color>{color}</color>
			<colorEnd>{colorend}</colorEnd>
		</image>

	</view>

	<view name="basic">

		<image name="basicgamelistbg" extra="true">
			<color>{color}</color>
			<colorEnd>{colorend}</colorEnd>
		</image>

	</view>

	<!-- dark mode draws the list text black: lighter tints of the colour keep it readable -->

	<view name="basic" ifSubset="darkmode:On">

		<image name="basicgamelistbg" extra="true">
			<color>{dark}</color>
			<colorEnd>{darkend}</colorEnd>
		</image>

	</view>

	<view name="detailed" ifSubset="darkmode:On">

		<image name="gamelistbg" extra="true">
			<color>{dark}</color>
			<colorEnd>{darkend}</colorEnd>
		</image>

		<image name="syscolorbar" extra="true">
			<color>{dark}</color>
		</image>

	</view>

	<view name="grid" ifSubset="darkmode:On">

		<image name="gamelistbg" extra="true">
			<color>{dark}</color>
			<colorEnd>{darkend}</colorEnd>
		</image>

	</view>

</theme>
"""


def luminance(rgb):
    lin = [(c / 255) / 12.92 if c / 255 <= 0.03928 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def dark_mode_tint(color, contrast=7.0):
    """Mix the colour with white until black text on it reaches the given contrast ratio."""
    rgb = mklogo.hexrgb(color)
    for i in range(21):
        t = i / 20
        mixed = tuple(round(c + (255 - c) * t) for c in rgb)
        if (luminance(mixed) + 0.05) / 0.05 >= contrast:
            return mklogo.rgbhex(mixed)
    return "FFFFFF"


def name_size(name):
    n = len(name)
    return "0.116" if n <= 10 else "0.095" if n <= 16 else "0.083" if n <= 28 else "0.07"


def article(word):
    return ("an " if word[0] in "aeiou" else "a ") + word


def write_system(folder, name, label, color, colorend, blurb, force):
    out = os.path.join(ROOT, folder)
    if os.path.isdir(out) and not force:
        return False
    os.makedirs(out, exist_ok=True)
    end = colorend or mklogo.rgbhex(mklogo.darken(mklogo.hexrgb(color), 0.35))
    with open(os.path.join(out, "theme.xml"), "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(name=escape(name), label=escape(label), blurb=escape(blurb),
                                color=color, colorend=end,
                                dark=dark_mode_tint(color), darkend=dark_mode_tint(end),
                                namesize=name_size(name)))
    mklogo.make_set(out, name, label, color, colorend)
    return True


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    force = "--force" in sys.argv
    tree = ET.parse(sys.argv[1])
    made = []
    for s in tree.getroot().iter("system"):
        g = lambda tag: (s.findtext(tag) or "").strip()
        folder = g("theme") or g("name")
        if not folder or re.search(r"[^a-z0-9_+.-]", folder):
            continue
        fullname, maker, year, hw = g("fullname"), g("manufacturer"), g("release"), g("hardware").lower()
        if folder in CURATED:
            name, label, color, colorend, blurb = CURATED[folder]
        else:
            name = fullname or folder
            label = ", ".join(x for x in (maker if maker not in ("", "None") else "", year if year not in ("", "None") else "") if x) or "Batocera"
            color, colorend = BY_HARDWARE.get(hw, "3A3D5C"), None
            blurb = None
        if not blurb:
            hwword = HW_WORD.get(hw, "system")
            blurb = "%s is %s%s%s." % (name, article(hwword),
                                       (" by " + maker) if maker and maker != "None" else "",
                                       (" first released in " + year) if year and year != "None" else "")
        if write_system(folder, name, label, color, colorend, blurb, force):
            made.append(folder)
    for folder, fullname in AUTO.items():
        name, label, color, colorend, blurb = CURATED[folder]
        if write_system(folder, name, label, color, colorend, blurb, force):
            made.append(folder)
    print("%d folders written: %s" % (len(made), " ".join(made)))


if __name__ == "__main__":
    main()
