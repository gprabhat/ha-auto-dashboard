# HA Auto Dashboard

A [HACS](https://hacs.xyz/) integration that discovers your Home Assistant areas, devices and entities, classifies them, and compiles that graph into ready-to-use Lovelace dashboards - no manual card-by-card configuration.

Author: Prabhat Giri

## Status

Early / actively developed. Phases 1-3 of the roadmap are implemented and covered by CI (pytest, hassfest, HACS validation):

- ✅ **Discovery engine** - reads the area/device/entity registries into an internal graph and classifies everything into Home / Rooms / Homelab / Security / Monitoring / Admin / Cloud
- ✅ **Dashboard compiler** - turns that graph into real Lovelace dashboard YAML
- ✅ **Dashboard installer** - writes the compiled dashboards to disk and tells you how to register them
- ⏳ Not yet built: fully automatic Lovelace registration (no manual step), a "Dashboard Studio" sidebar UI, preview/diff tooling

## What it generates

| Dashboard | Content |
|---|---|
| **Home** | A map of people/device trackers, an area-card grid for every room, a logbook of recent security/update activity |
| **Rooms** | One view per area, with a domain-appropriate card for every entity in that room |
| **Homelab** | One card group per homelab device (Proxmox, Docker, Vaultwarden, backups, ...), with numeric sensors (CPU/RAM/etc.) rendered as trend graphs |
| **Security** | Cameras as picture-glance cards (with sibling motion sensors overlaid), alarm/motion controls, a logbook of recent events |
| **Monitoring** | A combined history graph of network sensors (WAN speed, etc.) plus individual trend graphs |
| **Admin** | Update entities as actionable cards, plus an update history logbook |
| **Cloud** | Only generated if an area name contains "cloud" (e.g. a cloud/VPS host area) |

Cards are chosen per entity domain rather than falling back to a flat list: lights, climate, covers, fans, locks, media players, vacuums, alarms, people and updates each get their own [Mushroom](https://github.com/piitaya/lovelace-mushroom) card type, and numeric sensors get [mini-graph-card](https://github.com/kalkih/mini-graph-card) trend lines. Within a view, entities are grouped into titled boxes by domain (Lights, Climate & Covers, Media, Switches & Locks, Sensors, Other) instead of one long mixed list - switches and locks get a smaller column count than the rest so their tiles render noticeably bigger, since a simple toggle needs less detail per tile than a sensor graph.

### Frontend resources you need installed

The generated dashboards prefer these HACS **Frontend** resources (not part of this integration - install them separately via HACS):

- [Mushroom](https://github.com/piitaya/lovelace-mushroom)
- [Bubble Card](https://github.com/Clooos/Bubble-Card) (used for a couple of text separators; most section headings use the native `grid` card's own title instead)
- [mini-graph-card](https://github.com/kalkih/mini-graph-card)

The integration checks the Lovelace resources collection before generating: anything not detected as installed falls back to a native HA card instead (`tile`/`light`/`thermostat`/`media-control`/`alarm-panel`/`humidifier`/`heading`/`button`/`sensor` with an inline graph), so a dashboard never ships a "custom element doesn't exist" card. If something's missing, you'll see a **Repairs** issue in Settings listing exactly what to install - it clears itself automatically once detected. A [Material You](https://community.home-assistant.io/t/material-you-theme-and-utilities-a-fully-featured-implementation-of-material-design-3-expressive-for-home-assistant/623242)-style theme is recommended to match their look, but isn't required.

## Installation

### Via HACS (recommended)

1. HACS → the **⋮** menu (top right) → **Custom repositories**
2. Repository: `https://github.com/gprabhat/ha-auto-dashboard`, category **Integration**
3. Find "HA Auto Dashboard" in HACS → **Download**
4. Restart Home Assistant
5. Settings → Devices & Services → **Add Integration** → search "HA Auto Dashboard" (no configuration needed)

### Manual

Copy `custom_components/ha_auto_dashboard/` into `<config>/custom_components/ha_auto_dashboard/`, restart Home Assistant, then add the integration as above.

## Registering the generated dashboards (one-time step)

Home Assistant has no stable API for a custom integration to register a YAML-mode Lovelace dashboard at runtime, so after the first scan you'll get a **Repairs** issue in Settings ("Generated dashboards need one paste into configuration.yaml") containing a snippet like:

```yaml
lovelace:
  dashboards:
    auto-home:
      mode: yaml
      title: Home
      icon: mdi:home
      filename: dashboards/auto_home.yaml
    auto-rooms:
      mode: yaml
      title: Rooms
      icon: mdi:floor-plan
      filename: dashboards/auto_rooms.yaml
    # ...one entry per generated dashboard
```

Paste that into `configuration.yaml` and restart once. After that, every future scan just rewrites the same files in place - no further manual steps. The Repairs issue clears itself automatically once it detects the dashboards are registered.

## Actions

- `ha_auto_dashboard.scan` - re-discover areas/devices/entities and regenerate dashboards immediately (also runs automatically on startup, on registry changes, and every 6 hours as a safety net)
- `ha_auto_dashboard.generate` - recompile and rewrite the dashboards from the current graph, without doing a fresh scan

Diagnostics (Settings → Devices & Services → HA Auto Dashboard → Download diagnostics) expose the full discovered graph, classification stats, and a summary of the compiled dashboards.

## License

MIT
