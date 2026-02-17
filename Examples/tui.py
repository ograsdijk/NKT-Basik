from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional

import plotext as plt
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import CenterMiddle, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    RichLog,
    SelectionList,
    Static,
)

from nkt_basik import (
    Basik,
    ModulationCoupling,
    ModulationRange,
    ModulationSource,
    ModulationWaveform,
)


@dataclass(frozen=True)
class FieldSpec:
    label: str
    unit: str
    plot: bool


FIELD_SPECS: Dict[str, FieldSpec] = {
    "temperature": FieldSpec("Temperature", "C", True),
    "power": FieldSpec("Power", "mW", True),
    "wavelength": FieldSpec("Wavelength", "nm", True),
    "frequency": FieldSpec("Frequency", "GHz", True),
    "emission": FieldSpec("Emission", "", False),
    "status": FieldSpec("Status", "", False),
    "error": FieldSpec("Error", "", False),
    "mode": FieldSpec("Mode", "", False),
}

PLOT_FIELDS = [k for k, v in FIELD_SPECS.items() if v.plot]
POLL_FIELDS = list(FIELD_SPECS.keys())


@dataclass(frozen=True)
class InputCommandSpec:
    key: str
    label: str
    placeholder: str


INPUT_COMMANDS: list[InputCommandSpec] = [
    InputCommandSpec("set_wavelength", "Set Wavelength", "Wavelength setpoint (nm)"),
    InputCommandSpec("set_frequency", "Set Frequency", "Frequency setpoint (GHz)"),
    InputCommandSpec("set_power", "Set Power", "Power setpoint (mW)"),
    InputCommandSpec(
        "set_mod_source", "Set Modulation Source", "external / internal / both"
    ),
    InputCommandSpec("set_mod_range", "Set Modulation Range", "wide / narrow"),
    InputCommandSpec("set_mod_freq", "Set Modulation Frequency", "Frequency (Hz)"),
    InputCommandSpec("set_mod_coupling", "Set Modulation Coupling", "ac / dc"),
    InputCommandSpec(
        "set_mod_waveform",
        "Set Modulation Waveform",
        "sine / triangle / sawtooth / inverse_sawtooth",
    ),
    InputCommandSpec("move_freq", "Move Frequency", "Move frequency (GHz)"),
]


class CommandInputDialog(ModalScreen[tuple[str, str] | None]):
    def __init__(self, command: InputCommandSpec) -> None:
        super().__init__()
        self.command = command

    def compose(self) -> ComposeResult:
        with CenterMiddle():
            with Vertical(id="dialog"):
                yield Label(self.command.label, id="dialog_title")
                yield Input(placeholder=self.command.placeholder, id="dialog_input")
                with Horizontal(id="dialog_buttons"):
                    yield Button("Cancel", id="dialog_cancel")
                    yield Button("Send", id="dialog_submit", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#dialog_input", Input).focus()

    @on(Input.Submitted)
    def handle_submit(self, event: Input.Submitted) -> None:
        self._submit()

    @on(Button.Pressed)
    def handle_button(self, event: Button.Pressed) -> None:
        if event.button.id == "dialog_cancel":
            self.dismiss(None)
        elif event.button.id == "dialog_submit":
            self._submit()

    def _submit(self) -> None:
        value = self.query_one("#dialog_input", Input).value.strip()
        self.dismiss((self.command.key, value))


class LogView(RichLog):
    def __init__(self) -> None:
        super().__init__(
            id="log", max_lines=400, wrap=False, markup=False, auto_scroll=True
        )

    def append(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.write(f"[{timestamp}] {message}")


class PlotView(Static):
    def __init__(self) -> None:
        super().__init__("", id="plot", markup=False)
        self._series: Dict[str, list[float]] = {}
        self._times: Dict[str, list[float]] = {}

    def render_plot(
        self, series: Dict[str, list[float]], times: Dict[str, list[float]]
    ) -> None:
        self._series = series
        self._times = times
        self._draw()

    def on_resize(self) -> None:
        self._draw()

    def _draw(self) -> None:
        if self.size.width <= 0 or self.size.height <= 0:
            return

        plt.clear_figure()
        plt.clf()
        if hasattr(plt, "clear_data"):
            try:
                plt.clear_data()
            except Exception:
                pass
        if hasattr(plt, "clear_color"):
            try:
                plt.clear_color()
            except Exception:
                pass

        if not self._series:
            self.update(Text("(no data)", no_wrap=True))
            return

        width = self.size.width
        height = self.size.height
        if width < 10 or height < 6:
            self.update(Text("(plot area too small)", no_wrap=True))
            return

        if hasattr(plt, "plotsize"):
            try:
                plt.plotsize(width, height)
            except Exception:
                pass

        for name, values in self._series.items():
            tvals = self._times.get(name, [])
            if values and tvals and len(values) == len(tvals):
                plt.plot(tvals, values, label=name)

        plt.canvas_color("default")
        plt.axes_color("default")
        plt.ticks_color("default")
        plt.title("Live plot")
        plt.xlabel("time (s)")
        if len(self._series) > 1 and width >= 30 and hasattr(plt, "legend"):
            try:
                getattr(plt, "legend")()
            except Exception:
                pass
        plot = plt.build()
        if hasattr(plt, "uncolorize"):
            try:
                plot = plt.uncolorize(plot)
            except Exception:
                pass
        self.update(Text(plot, no_wrap=True, overflow="crop"))


class BasikTUI(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #main {
        height: 1fr;
    }
    #left {
        width: 40%;
        min-width: 36;
        border: solid $primary;
        padding: 1 1;
        overflow: auto;
        height: 1fr;
        scrollbar-gutter: stable;
    }
    #right {
        width: 1fr;
        border: solid $primary;
        padding: 1 1;
        height: 1fr;
    }
    #left > * {
        margin-bottom: 1;
    }
    #right > * {
        margin-bottom: 1;
    }
    #left Input, #left Button, #left SelectionList, #left OptionList {
        width: 1fr;
    }
    #left Horizontal {
        height: auto;
    }
    #log {
        height: 12;
        overflow: auto;
        border: solid $secondary;
        padding: 0 1;
    }
    #plot {
        height: 1fr;
        border: solid $secondary;
        padding: 0 1;
    }
    #table {
        height: 8;
        border: solid $secondary;
    }
    #poll_fields, #plot_fields {
        height: 6;
        border: solid $secondary;
    }
    #command_list {
        height: 12;
        border: solid $secondary;
    }
    #dialog {
        width: 70%;
        min-width: 40;
        border: solid $primary;
        background: $panel;
        padding: 1 2;
    }
    #dialog_title {
        text-style: bold;
    }
    #dialog_buttons {
        height: auto;
    }
    #dialog_buttons Button {
        width: 1fr;
    }
    .section-title {
        text-style: bold;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.device: Optional[Basik] = None
        self.poll_timer = None
        self.start_time = None
        self.history: Dict[str, Deque[float]] = {
            field: deque(maxlen=300) for field in PLOT_FIELDS
        }
        self.history_times: Dict[str, Deque[float]] = {
            field: deque(maxlen=300) for field in PLOT_FIELDS
        }
        self.latest_values: Dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Horizontal(id="main"):
            with VerticalScroll(id="left"):
                yield Label("Connection", classes="section-title")
                yield Label("Status: disconnected", id="connection_status")
                yield Input(placeholder="COM port (e.g. COM6)", id="port_input")
                yield Input(placeholder="Device ID (e.g. 1)", id="devid_input")
                with Horizontal():
                    yield Button("Connect", id="connect")
                    yield Button("Disconnect", id="disconnect")

                yield Label("Input commands", classes="section-title")
                yield OptionList(
                    *[spec.label for spec in INPUT_COMMANDS], id="command_list"
                )
                yield Label("Quick toggles", classes="section-title")
                with Horizontal():
                    yield Button("Emission ON", id="em_on")
                    yield Button("Emission OFF", id="em_off")
                with Horizontal():
                    yield Button("Modulation ON", id="mod_on")
                    yield Button("Modulation OFF", id="mod_off")
                with Horizontal():
                    yield Button("Mode CURRENT", id="mode_current")
                    yield Button("Mode POWER", id="mode_power")

                yield Label("Polling", classes="section-title")
                yield Input(placeholder="Poll interval (s)", id="poll_interval")
                yield SelectionList(
                    *[
                        (FIELD_SPECS[k].label, k, k in ["temperature", "power"])
                        for k in POLL_FIELDS
                    ],
                    id="poll_fields",
                )
                with Horizontal():
                    yield Button("Start", id="poll_start")
                    yield Button("Stop", id="poll_stop")

                yield Label("Plot selection", classes="section-title")
                yield SelectionList(
                    *[
                        (FIELD_SPECS[k].label, k, k in ["temperature", "power"])
                        for k in PLOT_FIELDS
                    ],
                    id="plot_fields",
                )

            with Vertical(id="right"):
                yield Label("Last poll: -", id="last_poll")
                yield PlotView()
                yield DataTable(id="table")
                yield LogView()

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.add_columns("Field", "Value")
        self.poll_timer = self.set_interval(1.0, self.poll_device, pause=True)

    def log_message(self, message: str) -> None:
        self.query_one(LogView).append(message)

    def update_connection_status(self) -> None:
        label = self.query_one("#connection_status", Label)
        if self.device is None:
            label.update("Status: disconnected")
        else:
            label.update("Status: connected")

    def selected_values(self, widget_id: str) -> list[str]:
        selection = self.query_one(widget_id, SelectionList)
        values: list[str] = []
        for item in selection.selected:
            value = getattr(item, "value", item)
            values.append(value)
        return values

    def is_connected(self) -> bool:
        return self.device is not None

    @on(Button.Pressed)
    def handle_button(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "connect":
            self.connect_device()
        elif btn_id == "disconnect":
            self.disconnect_device()
        elif btn_id == "em_on":
            self.set_emission(True)
        elif btn_id == "em_off":
            self.set_emission(False)
        elif btn_id == "mod_on":
            self.set_modulation(True)
        elif btn_id == "mod_off":
            self.set_modulation(False)
        elif btn_id == "mode_current":
            self.set_mode_current()
        elif btn_id == "mode_power":
            self.set_mode_power()
        elif btn_id == "poll_start":
            self.start_polling()
        elif btn_id == "poll_stop":
            self.stop_polling()

    @on(OptionList.OptionSelected, "#command_list")
    def handle_command_selected(self, event: OptionList.OptionSelected) -> None:
        command = INPUT_COMMANDS[event.option_index]
        self.push_screen(CommandInputDialog(command), self.handle_command_dialog_result)

    def handle_command_dialog_result(self, result: tuple[str, str] | None) -> None:
        if result is None:
            return
        command_id, value = result
        value = value.strip()
        if not value:
            label = self.get_command_label(command_id)
            self.log_message(f"{label} input required")
            return
        self.execute_input_command(command_id, value)

    def get_command_label(self, command_id: str) -> str:
        for command in INPUT_COMMANDS:
            if command.key == command_id:
                return command.label
        return command_id

    def execute_input_command(self, command_id: str, value: str) -> None:
        handlers = {
            "set_wavelength": self.set_wavelength,
            "set_frequency": self.set_frequency,
            "set_power": self.set_power,
            "set_mod_source": self.set_modulation_source,
            "set_mod_range": self.set_modulation_range,
            "set_mod_freq": self.set_modulation_frequency,
            "set_mod_coupling": self.set_modulation_coupling,
            "set_mod_waveform": self.set_modulation_waveform,
            "move_freq": self.move_frequency,
        }
        handler = handlers.get(command_id)
        if handler is None:
            self.log_message(f"Unknown command: {command_id}")
            return
        handler(value)

    def connect_device(self) -> None:
        if self.device is not None:
            self.log_message("Already connected")
            return
        port = self.query_one("#port_input", Input).value.strip()
        dev_id_text = self.query_one("#devid_input", Input).value.strip()
        if not port or not dev_id_text:
            self.log_message("Port and device ID required")
            return
        try:
            dev_id = int(dev_id_text)
            self.device = Basik(port, dev_id)
            self.log_message(f"Connected to {port}, devID {dev_id}")
            self.update_connection_status()
        except Exception as exc:
            self.log_message(f"Connect failed: {exc}")
            self.device = None
            self.update_connection_status()

    def disconnect_device(self) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.close()
        except Exception as exc:
            self.log_message(f"Disconnect error: {exc}")
        self.device = None
        self.log_message("Disconnected")
        self.update_connection_status()

    def set_emission(self, enable: bool) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.emission = enable
            self.log_message(f"Emission set to {enable}")
        except Exception as exc:
            self.log_message(f"Emission error: {exc}")

    def set_modulation(self, enable: bool) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.modulation = enable
            self.log_message(f"Modulation set to {enable}")
        except Exception as exc:
            self.log_message(f"Modulation error: {exc}")

    def set_mode_current(self) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.set_current_mode()
            self.log_message("Mode set to CURRENT")
        except Exception as exc:
            self.log_message(f"Mode error: {exc}")

    def set_mode_power(self) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.set_power_mode()
            self.log_message("Mode set to POWER")
        except Exception as exc:
            self.log_message(f"Mode error: {exc}")

    def set_wavelength(self, value: str) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.wavelength_setpoint = float(value)
            self.log_message(f"Wavelength setpoint -> {value} nm")
        except Exception as exc:
            self.log_message(f"Set wavelength error: {exc}")

    def set_frequency(self, value: str) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.frequency_setpoint = float(value)
            self.log_message(f"Frequency setpoint -> {value} GHz")
        except Exception as exc:
            self.log_message(f"Set frequency error: {exc}")

    def set_power(self, value: str) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.output_power_setpoint = float(value)
            self.log_message(f"Power setpoint -> {value} mW")
        except Exception as exc:
            self.log_message(f"Set power error: {exc}")

    def set_modulation_source(self, value: str) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.modulation_source = ModulationSource[value.upper()]
            self.log_message(f"Modulation source -> {value}")
        except Exception as exc:
            self.log_message(f"Set modulation source error: {exc}")

    def set_modulation_range(self, value: str) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.modulation_range = ModulationRange[value.upper()]
            self.log_message(f"Modulation range -> {value}")
        except Exception as exc:
            self.log_message(f"Set modulation range error: {exc}")

    def set_modulation_frequency(self, value: str) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.modulation_frequency = float(value)
            self.log_message(f"Modulation frequency -> {value} Hz")
        except Exception as exc:
            self.log_message(f"Set modulation frequency error: {exc}")

    def set_modulation_coupling(self, value: str) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.modulation_coupling = ModulationCoupling[value.upper()]
            self.log_message(f"Modulation coupling -> {value}")
        except Exception as exc:
            self.log_message(f"Set modulation coupling error: {exc}")

    def set_modulation_waveform(self, value: str) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.modulation_waveform = ModulationWaveform[value.upper()]
            self.log_message(f"Modulation waveform -> {value}")
        except Exception as exc:
            self.log_message(f"Set modulation waveform error: {exc}")

    def move_frequency(self, value: str) -> None:
        if self.device is None:
            self.log_message("Not connected")
            return
        try:
            self.device.move_frequency(float(value))
            self.log_message(f"Move frequency by {value} GHz")
        except Exception as exc:
            self.log_message(f"Move frequency error: {exc}")

    def start_polling(self) -> None:
        if self.poll_timer is None:
            return
        interval_text = self.query_one("#poll_interval", Input).value.strip()
        if interval_text:
            try:
                interval = float(interval_text)
                self.poll_timer.stop()
                self.poll_timer = self.set_interval(
                    interval, self.poll_device, pause=False
                )
            except Exception:
                self.log_message("Invalid poll interval; using default")
                self.poll_timer.resume()
        else:
            self.poll_timer.resume()
        self.start_time = time.monotonic()
        if self.device is None:
            self.log_message("Polling started (waiting for connection)")
        else:
            self.log_message("Polling started")

    def stop_polling(self) -> None:
        if self.poll_timer is not None:
            self.poll_timer.pause()
            self.log_message("Polling stopped")

    def poll_device(self) -> None:
        last_poll = self.query_one("#last_poll", Label)
        if self.device is None:
            last_poll.update("Last poll: - (not connected)")
            return
        poll_list = self.selected_values("#poll_fields")
        plot_list = self.selected_values("#plot_fields")

        if not poll_list:
            last_poll.update("Last poll: - (no fields selected)")
            return

        now = time.monotonic()
        if self.start_time is None:
            self.start_time = now
        elapsed = now - self.start_time
        last_poll.update(f"Last poll: {time.strftime('%H:%M:%S')}")

        table = self.query_one("#table", DataTable)
        table.clear()

        for field in poll_list:
            try:
                value = self.read_field(field)
                self.latest_values[field] = value
            except Exception as exc:
                self.latest_values[field] = f"ERR: {exc}"

        for field in poll_list:
            label = FIELD_SPECS[field].label
            unit = FIELD_SPECS[field].unit
            value = self.latest_values.get(field, "")
            if unit and value and not value.startswith("ERR"):
                display = f"{value} {unit}"
            else:
                display = value
            table.add_row(label, display)

        if plot_list:
            for field in plot_list:
                if field in self.history:
                    try:
                        numeric = float(self.read_field(field))
                        self.history[field].append(numeric)
                        self.history_times[field].append(elapsed)
                    except Exception:
                        pass

        series = {
            name: list(self.history[name]) for name in plot_list if name in self.history
        }
        times = {
            name: list(self.history_times[name])
            for name in plot_list
            if name in self.history_times
        }
        self.query_one(PlotView).render_plot(series, times)

    def read_field(self, field: str) -> str:
        if self.device is None:
            return ""
        if field == "status":
            return str(self.device.status)
        if field == "error":
            return str(self.device.error)
        if field == "mode":
            return str(self.device.mode)
        value = getattr(self.device, field)
        return str(value)


if __name__ == "__main__":
    BasikTUI().run()
