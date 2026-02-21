# Baby Buddy for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A Home Assistant custom integration for [Baby Buddy](https://github.com/babybuddy/babybuddy). Monitor your child's activities, add data entries, and control timers — all from within Home Assistant.

**Requires Baby Buddy 2.10.0 or newer.**

## Features

- **Dynamic entity discovery** — sensors, binary sensors, selects, and switches are automatically created based on Baby Buddy's metadata endpoint
- **Real-time MQTT updates** — subscribe to Baby Buddy's MQTT state topics for instant sensor updates without polling
- **Bulk API optimization** — fetches all sensor data in a single API call per child (BB 2.10.0+)
- **Zeroconf discovery** — automatically detects Baby Buddy instances on your local network
- **HA services** — add feedings, diaper changes, sleep entries, and more directly from HA automations
- **Timer control** — start and stop Baby Buddy timers via switch entities

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Go to the **three-dot menu** (top right) → **Custom repositories**.
3. Add `https://github.com/eyalmichon/ha-babybuddy` with category **Integration**.
4. Search for **Baby Buddy** in the Integrations section and click **Install**.
5. Restart Home Assistant.

### Manual

Copy the `custom_components/babybuddy` folder into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

### Automatic discovery (Zeroconf)

If Baby Buddy advertises itself via mDNS (`_babybuddy._tcp.local.`), Home Assistant will automatically detect it. You'll only need to provide your API key.

### Manual setup

Go to **Settings → Devices & Services → Add Integration → Baby Buddy** and enter:

| Parameter | Description |
| --------- | ----------- |
| Host | URL of your Baby Buddy instance (e.g. `http://192.168.1.50`) |
| Port | Port number (default: `8000`) |
| Path | Sub-path if Baby Buddy is behind a reverse proxy (default: empty) |
| API Key | From Baby Buddy → User Settings → API Key |

### Options

After setup, configure these options via the integration's **Configure** button:

| Option | Description | Default |
| ------ | ----------- | ------- |
| Temperature unit | Celsius or Fahrenheit | Celsius |
| Weight unit | kg, g, lb, or oz | kg |
| Feeding volume unit | mL or fl. oz. | mL |
| Update interval | Polling interval in seconds | 60 |
| Enable MQTT | Subscribe to Baby Buddy MQTT state topics for real-time updates | Off |
| MQTT topic prefix | Base topic for MQTT subscriptions | `babybuddy` |

### Reconfigure

To change the host, port, path, or API key after setup, use the **Reconfigure** option in the integration menu (no need to delete and re-add).

## Entities

All entities are dynamically created based on Baby Buddy's discovery metadata. The exact set depends on your Baby Buddy version.

### Sensors

| Sensor | Description |
| ------ | ----------- |
| **Child** | One per child — state is the child's date of birth |
| **Last [activity]** | Last diaper change, feeding, sleep, temperature, weight, BMI, height, head circumference, note, pumping, tummy time, and medication. State is a timestamp; attributes contain the full entry details. |
| **[Stat] today** | Daily statistics — feedings today, diaper changes today, sleep total today, minutes since last feeding/diaper change, etc. |

### Binary Sensors

| Binary Sensor | Description |
| ------------- | ----------- |
| **Medication overdue** | `on` when one or more medications are overdue |

### Switches

| Switch | Description |
| ------ | ----------- |
| **Timer** | One per child. Turn **on** to start a timer, turn **off** to stop/delete it. Timers can be linked to feeding, sleep, and tummy time entries. |

### Selects

| Select | Description |
| ------ | ----------- |
| **Feeding type** | Breast milk, Formula, Fortified breast milk, Solid food |
| **Feeding method** | Bottle, Left breast, Right breast, Both breasts, Self fed, Parent fed |
| **Diaper color** | Black, Brown, Green, Yellow |

Select entities are used as defaults when calling the corresponding services.

## Services

All services are dynamically registered from Baby Buddy's metadata. Below are the standard services.

### `babybuddy.add_child`

Add a new child.

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| first_name | yes | Baby's first name |
| last_name | yes | Baby's last name |
| birth_date | yes | Date of birth (`YYYY-MM-DD`) |

### `babybuddy.add_diaper_change`

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Child sensor entity |
| type | no | `Wet`, `Solid`, or `Wet and Solid` |
| time | no | Timestamp (must be in the past) |
| color | no | `Black`, `Brown`, `Green`, or `Yellow` |
| amount | no | Number of diapers |
| notes | no | Notes text |
| tags | no | List of tags |

### `babybuddy.add_feeding`

Feeding can be linked to an active timer.

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Timer switch entity |
| type | yes | `Breast milk`, `Formula`, `Fortified breast milk`, or `Solid food` |
| method | yes | `Bottle`, `Left breast`, `Right breast`, `Both breasts`, `Self fed`, or `Parent fed` |
| timer | no | `true` to use the active timer for start/end |
| start | no | Start time (ignored if timer is used) |
| end | no | End time (ignored if timer is used) |
| amount | no | Amount as integer |
| notes | no | Notes text |
| tags | no | List of tags |

### `babybuddy.add_sleep`

Sleep can be linked to an active timer.

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Timer switch entity |
| timer | no | `true` to use the active timer |
| start | no | Start time |
| end | no | End time |
| nap | no | `true` to mark as nap |
| notes | no | Notes text |
| tags | no | List of tags |

### `babybuddy.add_temperature`

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Child sensor entity |
| temperature | yes | Temperature value (float) |
| time | no | Recording time |
| notes | no | Notes text |
| tags | no | List of tags |

### `babybuddy.add_weight`

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Child sensor entity |
| weight | yes | Weight value (float) |
| date | no | Recording date (`YYYY-MM-DD`) |
| notes | no | Notes text |
| tags | no | List of tags |

### `babybuddy.add_height`

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Child sensor entity |
| height | yes | Height value (float) |
| date | no | Recording date (`YYYY-MM-DD`) |
| notes | no | Notes text |
| tags | no | List of tags |

### `babybuddy.add_head_circumference`

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Child sensor entity |
| head_circumference | yes | Value (float) |
| date | no | Recording date (`YYYY-MM-DD`) |
| notes | no | Notes text |
| tags | no | List of tags |

### `babybuddy.add_bmi`

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Child sensor entity |
| BMI | yes | BMI value (float) |
| date | no | Recording date (`YYYY-MM-DD`) |
| notes | no | Notes text |
| tags | no | List of tags |

### `babybuddy.add_note`

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Child sensor entity |
| notes | no | Note text |
| time | no | Recording time |
| tags | no | List of tags |

### `babybuddy.add_pumping`

Pumping can be linked to an active timer.

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Child sensor entity |
| amount | yes | Amount as integer |
| timer | no | `true` to use the active timer |
| start | no | Start time |
| end | no | End time |
| notes | no | Notes text |
| tags | no | List of tags |

### `babybuddy.add_tummy_time`

Tummy time can be linked to an active timer.

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Timer switch entity |
| timer | no | `true` to use the active timer |
| start | no | Start time |
| end | no | End time |
| milestone | no | Milestone text |
| tags | no | List of tags |

### `babybuddy.delete_last_entry`

Deletes the most recent entry for a given sensor.

> [!CAUTION]
> Calling this service on a **device** (which represents a child) will delete the last entry for **every** sensor on that child.

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Sensor entity to delete the last entry for |

### `babybuddy.start_timer`

| Attribute | Required | Description |
| --------- | :------: | ----------- |
| entity_id | yes | Timer switch entity |
| start | no | Start time (must be in the past) |
| name | no | Optional timer name |

## MQTT

When **Enable MQTT** is turned on in the integration options, the integration subscribes to Baby Buddy's MQTT state topics for real-time updates. This means sensors update instantly when activities are logged — no waiting for the next polling interval.

Baby Buddy publishes retained messages to topics like:

```
babybuddy/{child-slug}/feedings/state
babybuddy/{child-slug}/sleep/state
babybuddy/{child-slug}/stats/state
...
```

### MQTT discovery conflict

Baby Buddy has a built-in option to publish Home Assistant MQTT discovery configs, which creates a separate set of MQTT-based entities. If both that option and this integration are enabled, you'll get **duplicate entities**.

The integration detects this conflict and creates a **repair issue** in Home Assistant. If your Baby Buddy version supports it, the repair flow can automatically disable BB's discovery toggle for you.

## Compatibility

| Component | Minimum Version |
| --------- | --------------- |
| Baby Buddy | 2.10.0 |
| Home Assistant | 2025.1.0 |

## Development

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting. Run checks with:

```bash
ruff check custom_components/babybuddy/
ruff format --check custom_components/babybuddy/
```

Tests run against a live Baby Buddy instance (see `.devcontainer/` for the dev environment setup):

```bash
pytest tests/
```
