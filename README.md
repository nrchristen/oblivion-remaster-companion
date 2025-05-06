# Oblivion Remaster Companion

**ES4 Console Automation Tool**

---

### Project Overview

> I have zero knowledge in modding any Bethesda titles or modifying any UE5 games.  
> I wanted a simple console automation tool that can live independently from directly messing with the game files.  
> This is purely for fun.

---

### Installation

#### From Release

1. Go to the [Releases](https://github.com/yourusername/oblivion-remaster-companion/releases) tab
2. Download the latest `ES4RCompanion.exe` from the assets
3. Run the executable (requires Windows 10/11)

#### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/oblivion-remaster-companion.git
   cd oblivion-remaster-companion
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### GUI Mode

```bash
python app.py
```

#### CLI Mode

```bash
python app.py --cli
```

### Running Tests

```bash
python -m unittest discover tests
```

### Features

- **Item Management**

  - Add items to inventory
  - Browse items by categories
  - Save favorite items for quick access

- **NPC Spawning**

  - Spawn NPCs with customizable quantities
  - Save NPC spawn presets

- **Location Teleportation**

  - Teleport to predefined locations
  - Browse locations by categories

- **Battle Presets**

  - Create and save battle scenarios
  - Quick execution of battle presets

- **Utility Commands**

  - Ghost mode toggle
  - Walk mode toggle
  - Custom command execution

- **Dual Interface**
  - Modern GUI interface
  - Command-line interface (CLI) for advanced users

### Object ID Sources

- **For versions past `v0.1.2`**  
  Object IDs are sourced from:  
  🔗 [UESP Wiki - The Unofficial Elder Scrolls Pages](https://en.uesp.net)

- **For versions up to and including `v0.1.2`**  
  Object IDs were sourced from:  
  🔗 [RaiderKing - Oblivion Remastered Console Commands and IDs](https://raiderking.com/tes4-oblivion-remastered-all-console-commands-and-ids-items-spells)

### Requirements

- Windows 10/11
- Python 3.8+ (for source installation)
- Microsoft WebView2 Runtime (for GUI mode)
- Oblivion Remastered running
