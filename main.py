# -*- coding: utf-8 -*-
"""
ARCANE CLOCK — Analog clock built on a circular doubly linked list
==================================================================

Academic project for Data Structures.

* Language: pure Python.
* The only import in the project: ``import tkinter as tk``.
* Main structure: circular doubly linked list (HourNode + CircularDoublyLinkedList).
* Interface: Tkinter (Canvas, Frame, Label, Button, Text, Toplevel).
* All the code (identifiers, comments, docstrings) is written in English.
  Only the texts shown to the user in the Tkinter window are in Spanish.

File layout
-----------
1. ArcaneMath                -> sine, cosine and square root implemented by hand (no math module).
2. HourNode                  -> node with value, prev and next.
3. CircularDoublyLinkedList  -> the data structure holding the 12 hours.
4. ArcaneTime                -> time logic (h, min, s, AM/PM). Hours ALWAYS move by
                                following the links of the circular doubly linked list.
5. Stopwatch                 -> stopwatch logic (independent from the clock).
6. Palette, ArcaneButton, ArcanePanel -> reusable visual style.
7. ArcaneClock               -> main window: draws the clock and wires everything together.
8. run_self_tests()          -> automatic tests of the logic (also available from a button).

The system time and the milliseconds are obtained with the ``clock`` command of the Tcl
interpreter that Tkinter already includes (``root.tk.call("clock", ...)``). It is not a
hidden import: it is a documented call of the Tk object itself.
"""

import tkinter as tk


# =====================================================================================
# 1. OWN MATH (without importing math)
# =====================================================================================
class ArcaneMath:
    """Math functions implemented by hand to draw the clock."""

    PI = 3.141592653589793
    TWO_PI = 6.283185307179586

    @staticmethod
    def degrees_to_radians(degrees):
        """Converts degrees to radians: rad = degrees * PI / 180."""
        return degrees * ArcaneMath.PI / 180.0

    @staticmethod
    def normalize_radians(angle):
        """Brings any angle into the interval [-PI, PI] so the Taylor series stays accurate."""
        angle = angle % ArcaneMath.TWO_PI          # now in [0, 2PI)
        if angle > ArcaneMath.PI:
            angle -= ArcaneMath.TWO_PI             # now in (-PI, PI]
        return angle

    @staticmethod
    def sine(angle):
        """
        Sine using the Taylor series:
            sin(x) = x - x^3/3! + x^5/5! - x^7/7! + ...
        Each term is obtained from the previous one by multiplying by -x^2 / ((2n)(2n+1)).
        With |x| <= PI and 12 terms the error is smaller than 1e-12.
        """
        x = ArcaneMath.normalize_radians(angle)
        term = x
        total = x
        x_squared = x * x
        for n in range(1, 12):
            term *= -x_squared / ((2 * n) * (2 * n + 1))
            total += term
        return total

    @staticmethod
    def cosine(angle):
        """Cosine using the identity cos(x) = sin(x + PI/2)."""
        return ArcaneMath.sine(angle + ArcaneMath.PI / 2)

    @staticmethod
    def square_root(number):
        """Square root with Newton's method: x_(k+1) = (x_k + n / x_k) / 2."""
        if number < 0:
            raise ValueError("No existe raíz cuadrada real de un número negativo.")
        if number == 0:
            return 0.0
        estimate = number if number >= 1 else 1.0
        for _ in range(60):
            new_estimate = 0.5 * (estimate + number / estimate)
            if abs(new_estimate - estimate) < 1e-12:
                return new_estimate
            estimate = new_estimate
        return estimate

    @staticmethod
    def point_on_circle(cx, cy, radius, clock_degrees):
        """
        Point on a circle using "clock" angles:
        0° = 12 o'clock, 90° = 3, 180° = 6, 270° = 9 (clockwise).

        On the Canvas the y coordinate grows DOWNWARDS, therefore:
            x = cx + radius * sin(angle)
            y = cy - radius * cos(angle)
        """
        radians = ArcaneMath.degrees_to_radians(clock_degrees)
        x = cx + radius * ArcaneMath.sine(radians)
        y = cy - radius * ArcaneMath.cosine(radians)
        return x, y


# =====================================================================================
# 2. LIST NODE
# =====================================================================================
class HourNode:
    """Node of the circular doubly linked list. Represents one hour of the clock (1 to 12)."""

    def __init__(self, value):
        self.value = value          # hour number
        self.next = None            # reference to the next node (clockwise)
        self.prev = None            # reference to the previous node (counterclockwise)

    def __repr__(self):
        prev_value = self.prev.value if self.prev is not None else None
        next_value = self.next.value if self.next is not None else None
        return "HourNode({} | prev={} | next={})".format(self.value, prev_value, next_value)


# =====================================================================================
# 3. CIRCULAR DOUBLY LINKED LIST
# =====================================================================================
class CircularDoublyLinkedList:
    """
    Circular doubly linked list.

    - ``head`` points to the first node (hour 1).
    - The tail is ``head.prev`` (hour 12); it does not need to be stored separately.
    - No link is ever None: the last node points to the head and the head to the last node.
    """

    def __init__(self):
        self.head = None
        self.size = 0

    @classmethod
    def create_clock_hours(cls):
        """Creates the list with hours 1, 2, ..., 12 linked in a circle."""
        hour_list = cls()
        for hour in range(1, 13):
            hour_list.append(hour)
        return hour_list

    def is_empty(self):
        """Tells whether the list has no nodes."""
        return self.head is None

    def get_tail(self):
        """Returns the last node (head.prev) or None if the list is empty."""
        return None if self.head is None else self.head.prev

    def append(self, value):
        """
        Inserts a node at the end (between the tail and the head) keeping the list circular.
        Empty list: the node points to itself in both directions.
        Duplicate values are not allowed (an hour cannot exist twice).
        Returns the created node.
        """
        if self.find(value) is not None:
            raise ValueError("La hora {} ya existe en la lista.".format(value))
        new_node = HourNode(value)
        if self.head is None:
            new_node.next = new_node
            new_node.prev = new_node
            self.head = new_node
        else:
            tail = self.head.prev
            tail.next = new_node            # the old tail points to the new node
            new_node.prev = tail            # the new node points back to the old tail
            new_node.next = self.head       # the new node closes the circle towards the head
            self.head.prev = new_node       # the head points back to the new node
        self.size += 1
        return new_node

    def find(self, value):
        """
        Walks the list from the head following ``next`` for at most ``size`` steps.
        Returns the node with that value or None if it does not exist.
        """
        current = self.head
        for _ in range(self.size):
            if current.value == value:
                return current
            current = current.next
        return None

    def move_forward(self, value):
        """Returns the node after the one holding ``value`` (12 -> 1 thanks to circularity)."""
        node = self.find(value)
        if node is None:
            raise ValueError("La hora {} no está en la lista.".format(value))
        return node.next

    def move_backward(self, value):
        """Returns the node before the one holding ``value`` (1 -> 12 thanks to circularity)."""
        node = self.find(value)
        if node is None:
            raise ValueError("La hora {} no está en la lista.".format(value))
        return node.prev

    def traverse_forward(self, start=None):
        """
        Follows the ``next`` links from the head (or from hour ``start``)
        until a full lap is completed. Returns the visited values in order.
        """
        if self.head is None:
            return []
        first = self.head if start is None else self.find(start)
        if first is None:
            raise ValueError("La hora {} no está en la lista.".format(start))
        values = []
        current = first
        for _ in range(self.size):
            values.append(current.value)
            current = current.next
        return values

    def traverse_backward(self, start=None):
        """
        Follows the ``prev`` links from the tail (or from hour ``start``)
        until a full lap is completed. Returns the visited values in order.
        """
        if self.head is None:
            return []
        first = self.head.prev if start is None else self.find(start)
        if first is None:
            raise ValueError("La hora {} no está en la lista.".format(start))
        values = []
        current = first
        for _ in range(self.size):
            values.append(current.value)
            current = current.prev
        return values

    def verify_integrity(self):
        """
        Checks that the structure is a valid circular doubly linked list:
          1. No link is None.
          2. For every node: node.next.prev is node and node.prev.next is node.
          3. After ``size`` steps forward we are back exactly at the head (and not earlier).
          4. After ``size`` steps backward we are also back at the head.
        Returns a tuple (is_valid, message). The message is shown in the interface,
        so it is written in Spanish.
        """
        if self.head is None:
            if self.size == 0:
                return True, "La lista está vacía y su tamaño es 0."
            return False, "La cabeza es None pero el tamaño registrado es {}.".format(self.size)

        errors = []
        current = self.head
        for step in range(self.size):
            if current.next is None or current.prev is None:
                errors.append("El nodo {} tiene un enlace nulo.".format(current.value))
                break
            if current.next.prev is not current:
                errors.append("{0}.next.prev no apunta a {0}.".format(current.value))
            if current.prev.next is not current:
                errors.append("{0}.prev.next no apunta a {0}.".format(current.value))
            current = current.next
            if current is self.head and step < self.size - 1:
                errors.append("Se volvió a la cabeza tras {} nodos; se esperaban {}.".format(
                    step + 1, self.size))
                break

        if not errors and current is not self.head:
            errors.append("Tras {} pasos hacia adelante no se volvió a la cabeza.".format(self.size))

        if not errors:
            current = self.head
            for _ in range(self.size):
                current = current.prev
            if current is not self.head:
                errors.append("Tras {} pasos hacia atrás no se volvió a la cabeza.".format(self.size))

        if errors:
            return False, " ".join(errors)
        return True, ("{} nodos; todos los enlaces prev/next son coherentes y el "
                      "círculo se cierra en ambos sentidos.").format(self.size)

    def get_size(self):
        """Returns the number of nodes in the list."""
        return self.size


# =====================================================================================
# 4. TIME LOGIC (separated from the interface)
# =====================================================================================
class ArcaneTime:
    """
    Stores the clock time. The hour is NOT a plain integer: it is a reference to an
    HourNode of the list. To change it, the list's move_forward() and move_backward() are used.
    """

    def __init__(self, hour_list):
        self.hour_list = hour_list
        self.hour_node = hour_list.find(12)
        self.minutes = 0
        self.seconds = 0
        self.is_pm = False

    @property
    def hour(self):
        """Value (1-12) of the current node."""
        return self.hour_node.value

    def set_time(self, hour_24, minutes, seconds):
        """Sets the time from a 24 h format by finding the matching node."""
        if not (0 <= hour_24 <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
            raise ValueError("Hora fuera de rango.")
        value = hour_24 % 12
        if value == 0:
            value = 12
        node = self.hour_list.find(value)
        if node is None:
            raise ValueError("La lista no contiene la hora {}.".format(value))
        self.hour_node = node
        self.is_pm = hour_24 >= 12
        self.minutes = minutes
        self.seconds = seconds

    def hour_24(self):
        """Converts the node hour + AM/PM to 24 h format."""
        if self.is_pm:
            return 12 if self.hour == 12 else self.hour + 12
        return 0 if self.hour == 12 else self.hour

    def next_hour(self):
        """Moves to the next node. Going from 11 to 12 toggles AM <-> PM."""
        if self.hour == 11:
            self.is_pm = not self.is_pm
        self.hour_node = self.hour_list.move_forward(self.hour)

    def previous_hour(self):
        """Moves to the previous node. Going from 12 to 11 toggles AM <-> PM."""
        if self.hour == 12:
            self.is_pm = not self.is_pm
        self.hour_node = self.hour_list.move_backward(self.hour)

    def add_minute(self):
        """Adds one minute; 59 becomes 00 and the hour moves forward."""
        if self.minutes == 59:
            self.minutes = 0
            self.next_hour()
        else:
            self.minutes += 1

    def subtract_minute(self):
        """Subtracts one minute; 00 becomes 59 and the hour moves backward."""
        if self.minutes == 0:
            self.minutes = 59
            self.previous_hour()
        else:
            self.minutes -= 1

    def add_second(self):
        """Adds one second; 59 becomes 00 and one minute is added."""
        if self.seconds == 59:
            self.seconds = 0
            self.add_minute()
        else:
            self.seconds += 1

    def angles(self):
        """
        Hand angles (degrees from 12 o'clock, clockwise):
            seconds = s * 6
            minutes = m * 6 + s * 0.1          (6° per minute / 60 s)
            hours   = (h % 12) * 30 + m * 0.5 + s * (0.5 / 60)
        """
        s = self.seconds
        m = self.minutes
        h = self.hour % 12
        second_angle = s * 6.0
        minute_angle = m * 6.0 + s * 0.1
        hour_angle = h * 30.0 + m * 0.5 + s * (0.5 / 60.0)
        return hour_angle, minute_angle, second_angle

    def period(self):
        """Returns "AM" or "PM"."""
        return "PM" if self.is_pm else "AM"

    def text_12h(self):
        """Time as HH:MM:SS (12 h)."""
        return "{:02d}:{:02d}:{:02d}".format(self.hour, self.minutes, self.seconds)

    def text_24h(self):
        """Time as HH:MM:SS (24 h)."""
        return "{:02d}:{:02d}:{:02d}".format(self.hour_24(), self.minutes, self.seconds)


# =====================================================================================
# 5. STOPWATCH LOGIC (independent from the clock)
# =====================================================================================
class Stopwatch:
    """
    Stopwatch based on millisecond timestamps.
    ``ms_source`` is a function that returns the current milliseconds; this way the class
    does not depend on the interface and can be tested with a fake clock.
    """

    def __init__(self, ms_source):
        self._ms_source = ms_source
        self.running = False
        self._accumulated_ms = 0
        self._start_ms = 0

    def start(self):
        """Starts counting. If it is already running it returns False and does nothing (avoids duplicates)."""
        if self.running:
            return False
        self._start_ms = self._ms_source()
        self.running = True
        return True

    def pause(self):
        """Pauses and stores the accumulated time. Returns False if it was already paused."""
        if not self.running:
            return False
        self._accumulated_ms += self._ms_source() - self._start_ms
        self.running = False
        return True

    def reset(self):
        """Stops the stopwatch and sets it back to 00:00:00."""
        self.running = False
        self._accumulated_ms = 0
        self._start_ms = 0

    def elapsed_ms(self):
        """Total measured milliseconds."""
        if self.running:
            return self._accumulated_ms + (self._ms_source() - self._start_ms)
        return self._accumulated_ms

    def text(self):
        """Time as HH:MM:SS."""
        total_seconds = self.elapsed_ms() // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

    def tenths(self):
        """Current tenth of a second (0-9), for a visual detail."""
        return (self.elapsed_ms() % 1000) // 100


# =====================================================================================
# 6. VISUAL STYLE
# =====================================================================================
class Palette:
    """Application colors and fonts."""
    BACKGROUND = "#0a1324"
    BACKGROUND_HIGH = "#0e1a31"
    PANEL = "#122039"
    PANEL_BORDER = "#22385f"
    BUTTON = "#1b2d4f"
    BUTTON_HOVER = "#26426f"
    DIAL = "#0d1a30"
    DIAL_RING = "#16294a"
    TURQUOISE = "#34e0cf"
    TURQUOISE_DARK = "#168a82"
    TURQUOISE_HOVER = "#1ea79d"
    GOLD = "#e9b949"
    GOLD_HOVER = "#f6cf70"
    GOLD_DARK = "#8a6c27"
    TEXT = "#e6edf7"
    TEXT_SOFT = "#93a7c6"
    TEXT_DIM = "#5d7194"
    SUCCESS = "#3ee08f"
    ERROR = "#ff6b6b"
    WARNING = "#f6c35b"
    FONT = "Segoe UI"
    MONO = "Consolas"


class ArcaneButton(tk.Button):
    """Flat button with palette colors and a hover effect."""

    STYLES = {
        "normal": (Palette.BUTTON, Palette.TEXT, Palette.BUTTON_HOVER),
        "primary": (Palette.TURQUOISE_DARK, "#ffffff", Palette.TURQUOISE_HOVER),
        "gold": (Palette.GOLD, Palette.BACKGROUND, Palette.GOLD_HOVER),
    }

    def __init__(self, parent, text, command, style="normal"):
        background, foreground, highlight = self.STYLES[style]
        super().__init__(
            parent, text=text, command=command, bg=background, fg=foreground,
            activebackground=highlight, activeforeground=foreground,
            disabledforeground=Palette.TEXT_DIM, relief="flat", bd=0,
            highlightthickness=0, padx=8, pady=6, cursor="hand2",
            font=(Palette.FONT, 9, "bold"),
        )
        self._background = background
        self._highlight = highlight
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event):
        if str(self["state"]) != "disabled":
            self.configure(bg=self._highlight)

    def _on_leave(self, _event):
        self.configure(bg=self._background)

    def set_enabled(self, enabled):
        """Enables or disables the button while keeping its style."""
        self.configure(state="normal" if enabled else "disabled",
                       cursor="hand2" if enabled else "arrow")
        if not enabled:
            self.configure(bg=Palette.BACKGROUND_HIGH)
        else:
            self.configure(bg=self._background)


class ArcanePanel(tk.Frame):
    """Panel with a thin border, a title with a gold accent and a ``content`` area."""

    def __init__(self, parent, title, subtitle=None):
        super().__init__(parent, bg=Palette.PANEL, highlightthickness=1,
                         highlightbackground=Palette.PANEL_BORDER,
                         highlightcolor=Palette.PANEL_BORDER)
        header = tk.Frame(self, bg=Palette.PANEL)
        header.pack(fill="x", padx=14, pady=(8, 0))
        tk.Frame(header, bg=Palette.GOLD, width=4, height=16).pack(side="left", padx=(0, 8))
        tk.Label(header, text=title.upper(), bg=Palette.PANEL, fg=Palette.TEXT,
                 font=(Palette.FONT, 10, "bold")).pack(side="left")
        if subtitle:
            tk.Label(header, text=subtitle, bg=Palette.PANEL, fg=Palette.TEXT_DIM,
                     font=(Palette.FONT, 9)).pack(side="left", padx=(10, 0))
        self.content = tk.Frame(self, bg=Palette.PANEL)
        self.content.pack(fill="both", expand=True, padx=14, pady=(6, 10))


# =====================================================================================
# 7. MAIN APPLICATION
# =====================================================================================
class ArcaneClock:
    """Main window: analog clock, time panel, adjustments, list, stopwatch and information."""

    CLOCK_INTERVAL_MS = 100           # how often the clock is checked (does not freeze the window)
    STOPWATCH_INTERVAL_MS = 50        # stopwatch refresh rate
    ANIMATION_STEP_MS = 260           # speed of the traversal animation

    def __init__(self, root):
        self.root = root

        # --- Logic (no interface) ---
        self.hour_list = CircularDoublyLinkedList.create_clock_hours()
        self.time = ArcaneTime(self.hour_list)
        self.stopwatch = Stopwatch(self._system_milliseconds)

        # --- Internal state ---
        self.paused = False
        self._last_ms = None
        self._accumulated_ms = 0
        self._pulse_counter = 0
        self._clock_loop_id = None
        self._stopwatch_loop_id = None
        self._animation_id = None
        self._traversal_node = None
        self._drawn_hour = None
        self._clock_geometry = None
        self._last_integrity = None

        # --- Interface text variables ---
        self.var_digital_time = tk.StringVar(value="--:--:--")
        self.var_period = tk.StringVar(value="--")
        self.var_time_detail = tk.StringVar(value="")
        self.var_stopwatch = tk.StringVar(value="00:00:00")
        self.var_tenths = tk.StringVar(value=".0")
        self.var_stopwatch_state = tk.StringVar(value="Detenido")
        self.var_node = tk.StringVar(value="")
        self.var_traversal = tk.StringVar(value="Pulsa un recorrido para ver cómo se siguen los enlaces.")
        self.var_integrity = tk.StringVar(value="Sin verificar")
        self.var_size = tk.StringVar(value="")
        self.var_last_check = tk.StringVar(value="Última verificación: pendiente")
        self.var_status = tk.StringVar(value="")
        self.var_indicator = tk.StringVar(value="EN MARCHA")

        self._configure_window()
        self._build_interface()

        self.sync_with_system(announce=False)
        self.verify_integrity(announce=False)
        self._refresh_stopwatch_view()
        self.show_status("Reloj iniciado y sincronizado con la hora del sistema. "
                         "Lista circular doble creada con 12 nodos.", "success")
        self._clock_loop()

    # ------------------------------------------------------------------ window
    def _configure_window(self):
        self.root.title("RELOJ ARCANO — Reloj analógico con lista circular doble")
        self.root.configure(bg=Palette.BACKGROUND)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = min(1320, screen_width - 40)
        height = min(800, screen_height - 80)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2 - 20)
        self.root.geometry("{}x{}+{}+{}".format(width, height, x, y))
        self.root.minsize(1140, 660)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.report_callback_exception = self._report_error
        self._create_icon()

    def _create_icon(self):
        """Draws a 32x32 pixel icon with PhotoImage (no external files)."""
        try:
            size = 32
            icon = tk.PhotoImage(width=size, height=size)
            center = (size - 1) / 2.0
            for row in range(size):
                colors = []
                for column in range(size):
                    dx = column - center
                    dy = row - center
                    distance_sq = dx * dx + dy * dy
                    if distance_sq > 15.5 * 15.5:
                        colors.append(Palette.BACKGROUND)
                    elif distance_sq > 12.5 * 12.5:
                        colors.append(Palette.GOLD)
                    elif abs(dx) <= 1 and -10 <= dy <= 0:
                        colors.append(Palette.TURQUOISE)
                    elif abs(dy) <= 1 and 0 <= dx <= 7:
                        colors.append(Palette.GOLD)
                    else:
                        colors.append(Palette.DIAL)
                icon.put("{" + " ".join(colors) + "}", to=(0, row))
            self._icon = icon
            self.root.iconphoto(True, icon)
        except tk.TclError:
            pass

    # ------------------------------------------------------------------ construction
    def _build_interface(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self._build_header()

        body = tk.Frame(self.root, bg=Palette.BACKGROUND)
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(10, 6))
        body.rowconfigure(0, weight=1)
        # "uniform" makes the widths keep the 4 : 3 : 4 ratio
        body.columnconfigure(0, weight=4, uniform="columns")
        body.columnconfigure(1, weight=3, uniform="columns")
        body.columnconfigure(2, weight=4, uniform="columns")

        # Column 0: analog clock
        clock_panel = ArcanePanel(body, "Reloj analógico")
        clock_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.clock_canvas = tk.Canvas(clock_panel.content, bg=Palette.PANEL,
                                      highlightthickness=0, width=360, height=360)
        self.clock_canvas.pack(fill="both", expand=True)
        self.clock_canvas.bind("<Configure>", self._draw_dial)

        # Column 1: time, adjustments, stopwatch
        control_column = tk.Frame(body, bg=Palette.BACKGROUND)
        control_column.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        control_column.columnconfigure(0, weight=1)
        self._build_time_panel(control_column).grid(row=0, column=0, sticky="ew")
        self._build_adjust_panel(control_column).grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self._build_stopwatch_panel(control_column).grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self._build_info_panel(control_column).grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        control_column.rowconfigure(3, weight=1)

        # Column 2: circular doubly linked list
        self._build_list_panel(body).grid(row=0, column=2, sticky="nsew")

        self._build_status_bar()

    def _build_header(self):
        header = tk.Frame(self.root, bg=Palette.BACKGROUND_HIGH)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        logo = tk.Canvas(header, width=46, height=46, bg=Palette.BACKGROUND_HIGH, highlightthickness=0)
        logo.grid(row=0, column=0, rowspan=2, padx=(18, 12), pady=8)
        logo.create_oval(4, 4, 42, 42, outline=Palette.GOLD, width=2)
        logo.create_oval(9, 9, 37, 37, outline=Palette.TURQUOISE_DARK, width=1)
        for hour in range(12):
            x1, y1 = ArcaneMath.point_on_circle(23, 23, 15, hour * 30)
            logo.create_oval(x1 - 1, y1 - 1, x1 + 1, y1 + 1, fill=Palette.TEXT_SOFT, outline="")
        logo.create_line(23, 23, 23, 12, fill=Palette.TURQUOISE, width=2, capstyle="round")
        logo.create_line(23, 23, 31, 23, fill=Palette.GOLD, width=3, capstyle="round")
        logo.create_oval(21, 21, 25, 25, fill=Palette.GOLD, outline="")

        tk.Label(header, text="RELOJ ARCANO", bg=Palette.BACKGROUND_HIGH, fg=Palette.TEXT,
                 font=(Palette.FONT, 19, "bold")).grid(row=0, column=1, sticky="sw", pady=(8, 0))
        tk.Label(header,
                 text="Reloj analógico cuyas 12 horas viven en una lista doblemente enlazada circular",
                 bg=Palette.BACKGROUND_HIGH, fg=Palette.TEXT_SOFT,
                 font=(Palette.FONT, 10)).grid(row=1, column=1, sticky="nw", pady=(0, 8))

        ArcaneButton(header, "Ejecutar autopruebas", self.show_self_tests).grid(
            row=0, column=2, rowspan=2, padx=(10, 0))
        indicator = tk.Frame(header, bg=Palette.PANEL, highlightthickness=1,
                             highlightbackground=Palette.PANEL_BORDER)
        indicator.grid(row=0, column=3, rowspan=2, padx=18)
        self.pulse_canvas = tk.Canvas(indicator, width=16, height=16, bg=Palette.PANEL, highlightthickness=0)
        self.pulse_canvas.pack(side="left", padx=(10, 6), pady=8)
        self.pulse_canvas.create_oval(2, 2, 14, 14, fill=Palette.SUCCESS, outline="", tags="pulse")
        self.indicator_label = tk.Label(indicator, textvariable=self.var_indicator, bg=Palette.PANEL,
                                        fg=Palette.SUCCESS, font=(Palette.FONT, 10, "bold"))
        self.indicator_label.pack(side="left", padx=(0, 12))

        tk.Frame(self.root, bg=Palette.TURQUOISE_DARK, height=2).grid(row=0, column=0, sticky="sew")

    def _build_time_panel(self, parent):
        panel = ArcanePanel(parent, "Hora actual")
        c = panel.content
        row = tk.Frame(c, bg=Palette.PANEL)
        row.pack(fill="x")
        tk.Label(row, textvariable=self.var_digital_time, bg=Palette.PANEL, fg=Palette.TURQUOISE,
                 font=(Palette.MONO, 26, "bold")).pack(side="left")
        tk.Label(row, textvariable=self.var_period, bg=Palette.PANEL, fg=Palette.GOLD,
                 font=(Palette.FONT, 14, "bold")).pack(side="left", padx=(8, 0), anchor="s", pady=(0, 6))
        tk.Label(c, textvariable=self.var_time_detail, bg=Palette.PANEL, fg=Palette.TEXT_SOFT,
                 font=(Palette.FONT, 9), anchor="w").pack(fill="x", pady=(0, 8))

        buttons = tk.Frame(c, bg=Palette.PANEL)
        buttons.pack(fill="x")
        for column in range(3):
            buttons.columnconfigure(column, weight=1, uniform="time")
        self.pause_button = ArcaneButton(buttons, "Pausar", self.pause_clock, "gold")
        self.pause_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.resume_button = ArcaneButton(buttons, "Reanudar", self.resume_clock, "primary")
        self.resume_button.grid(row=0, column=1, sticky="ew", padx=4)
        self.sync_button = ArcaneButton(buttons, "Sincronizar", self.sync_with_system)
        self.sync_button.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        self.resume_button.set_enabled(False)
        return panel

    def _build_adjust_panel(self, parent):
        panel = ArcanePanel(parent, "Ajuste manual")
        c = panel.content
        grid = tk.Frame(c, bg=Palette.PANEL)
        grid.pack(fill="x")
        actions = (("+1 hora", self.add_hour), ("−1 hora", self.subtract_hour),
                   ("+1 min", self.add_minute), ("−1 min", self.subtract_minute))
        for column, (text, command) in enumerate(actions):
            grid.columnconfigure(column, weight=1, uniform="adjust")
            ArcaneButton(grid, text, command).grid(
                row=0, column=column, sticky="ew", padx=(0 if column == 0 else 3, 0 if column == 3 else 3))
        return panel

    def _build_stopwatch_panel(self, parent):
        panel = ArcanePanel(parent, "Cronómetro")
        c = panel.content
        row = tk.Frame(c, bg=Palette.PANEL)
        row.pack(fill="x")
        tk.Label(row, textvariable=self.var_stopwatch, bg=Palette.PANEL, fg=Palette.GOLD,
                 font=(Palette.MONO, 22, "bold")).pack(side="left")
        tk.Label(row, textvariable=self.var_tenths, bg=Palette.PANEL, fg=Palette.GOLD_DARK,
                 font=(Palette.MONO, 13, "bold")).pack(side="left", anchor="s", pady=(0, 5))
        self.stopwatch_state_label = tk.Label(row, textvariable=self.var_stopwatch_state, bg=Palette.PANEL,
                                              fg=Palette.TEXT_DIM, font=(Palette.FONT, 9, "bold"))
        self.stopwatch_state_label.pack(side="left", anchor="s", padx=(10, 0), pady=(0, 6))

        buttons = tk.Frame(c, bg=Palette.PANEL)
        buttons.pack(fill="x", pady=(8, 0))
        for column in range(3):
            buttons.columnconfigure(column, weight=1, uniform="stopwatch")
        self.stopwatch_start_button = ArcaneButton(buttons, "Iniciar", self.start_stopwatch, "primary")
        self.stopwatch_start_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.stopwatch_pause_button = ArcaneButton(buttons, "Pausar", self.pause_stopwatch, "gold")
        self.stopwatch_pause_button.grid(row=0, column=1, sticky="ew", padx=4)
        self.stopwatch_reset_button = ArcaneButton(buttons, "Reiniciar", self.reset_stopwatch)
        self.stopwatch_reset_button.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        return panel

    def _build_list_panel(self, parent):
        panel = ArcanePanel(parent, "Lista circular doble", "1 ⇄ 2 ⇄ … ⇄ 12 ⇄ 1")
        c = panel.content

        self.list_canvas = tk.Canvas(c, bg=Palette.PANEL, highlightthickness=0, width=330, height=230)
        self.list_canvas.pack(fill="both", expand=True)
        self.list_canvas.bind("<Configure>", self._draw_list)

        legend = tk.Frame(c, bg=Palette.PANEL)
        legend.pack(fill="x", pady=(2, 4))
        current_node_text = "nodo de la hora actual"
        for color, text in ((Palette.TURQUOISE, "siguiente"), (Palette.GOLD, "anterior"),
                            (Palette.TURQUOISE_DARK, current_node_text)):
            sample = tk.Canvas(legend, width=26, height=12, bg=Palette.PANEL, highlightthickness=0)
            sample.pack(side="left")
            if text == current_node_text:
                sample.create_oval(8, 1, 18, 11, fill=Palette.TURQUOISE, outline="")
            else:
                sample.create_line(2, 6, 24, 6, fill=color, width=2, arrow="last", arrowshape=(6, 7, 3))
            tk.Label(legend, text=text, bg=Palette.PANEL, fg=Palette.TEXT_SOFT,
                     font=(Palette.FONT, 8)).pack(side="left", padx=(2, 10))

        tk.Label(c, textvariable=self.var_node, bg=Palette.BACKGROUND_HIGH, fg=Palette.TEXT,
                 font=(Palette.MONO, 10), anchor="w", padx=8, pady=5).pack(fill="x", pady=(0, 8))

        grid = tk.Frame(c, bg=Palette.PANEL)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="list")
        grid.columnconfigure(1, weight=1, uniform="list")
        ArcaneButton(grid, "◀  Hora anterior", self.go_previous_hour).grid(
            row=0, column=0, sticky="ew", padx=(0, 4), pady=(0, 6))
        ArcaneButton(grid, "Hora siguiente  ▶", self.go_next_hour).grid(
            row=0, column=1, sticky="ew", padx=(4, 0), pady=(0, 6))
        ArcaneButton(grid, "Recorrer adelante →", self.traverse_forward).grid(
            row=1, column=0, sticky="ew", padx=(0, 4), pady=(0, 6))
        ArcaneButton(grid, "← Recorrer atrás", self.traverse_backward).grid(
            row=1, column=1, sticky="ew", padx=(4, 0), pady=(0, 6))
        ArcaneButton(grid, "Verificar integridad", self.verify_integrity, "primary").grid(
            row=2, column=0, columnspan=2, sticky="ew")

        integrity_row = tk.Frame(c, bg=Palette.PANEL)
        integrity_row.pack(fill="x", pady=(8, 2))
        self.integrity_canvas = tk.Canvas(integrity_row, width=14, height=14, bg=Palette.PANEL,
                                          highlightthickness=0)
        self.integrity_canvas.pack(side="left", padx=(0, 6))
        self.integrity_canvas.create_oval(2, 2, 12, 12, fill=Palette.TEXT_DIM, outline="", tags="dot")
        self.integrity_label = tk.Label(integrity_row, textvariable=self.var_integrity, bg=Palette.PANEL,
                                        fg=Palette.TEXT_SOFT, font=(Palette.FONT, 10, "bold"), anchor="w")
        self.integrity_label.pack(side="left", fill="x")

        self.traversal_label = tk.Label(c, textvariable=self.var_traversal, bg=Palette.PANEL,
                                        fg=Palette.TEXT_SOFT, font=(Palette.MONO, 9), anchor="w",
                                        justify="left", wraplength=340)
        self.traversal_label.pack(fill="x")
        c.bind("<Configure>", lambda e: self.traversal_label.configure(wraplength=max(200, e.width - 6)))
        return panel

    def _build_info_panel(self, parent):
        panel = ArcanePanel(parent, "Información técnica")
        c = panel.content
        tk.Label(c, textvariable=self.var_size, bg=Palette.PANEL, fg=Palette.TEXT,
                 font=(Palette.FONT, 9, "bold"), anchor="w").pack(fill="x")
        self.last_check_label = tk.Label(
            c, textvariable=self.var_last_check, bg=Palette.PANEL, fg=Palette.TEXT_SOFT,
            font=(Palette.FONT, 9), anchor="w")
        self.last_check_label.pack(fill="x", pady=(0, 6))
        text_frame = tk.Frame(c, bg=Palette.BACKGROUND_HIGH)
        text_frame.pack(fill="both", expand=True)
        text_box = tk.Text(text_frame, width=30, height=2, wrap="word", bg=Palette.BACKGROUND_HIGH,
                           fg=Palette.TEXT_SOFT, font=(Palette.FONT, 9), relief="flat", bd=0, padx=8, pady=6,
                           highlightthickness=0, cursor="arrow")
        scrollbar = tk.Scrollbar(text_frame, command=text_box.yview, width=10)
        text_box.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text_box.pack(side="left", fill="both", expand=True)
        text_box.tag_configure("title", foreground=Palette.GOLD, font=(Palette.FONT, 9, "bold"))
        sections = (
            ("¿Qué es una lista circular doble?",
             "Una colección de nodos donde cada uno conoce a su vecino anterior y a su vecino "
             "siguiente, y el último se une con el primero: no existe un final con None."),
            ("¿Qué representa cada nodo?",
             "Cada nodo (clase HourNode) guarda una hora del reloj (valor 1 a 12)."),
            ("Enlaces anterior (prev) y siguiente (next)",
             "next lleva a la hora posterior (sentido horario) y prev a la hora previa "
             "(sentido antihorario). Permiten moverse y recorrer en ambos sentidos."),
            ("¿Por qué es circular?",
             "Porque el reloj lo es: después de las 12 vienen las 1 (12.next = 1) y antes de "
             "las 1 están las 12 (1.prev = 12)."),
            ("Uso en el reloj",
             "La hora actual es una referencia a un nodo HourNode. Avanzar o retroceder la hora, los "
             "números de la esfera y el diagrama se obtienen siguiendo esos enlaces."),
        )
        for title, body in sections:
            text_box.insert("end", title + "\n", "title")
            text_box.insert("end", body + "\n\n")
        text_box.configure(state="disabled")

        return panel

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=Palette.BACKGROUND_HIGH)
        bar.grid(row=2, column=0, sticky="ew")
        bar.columnconfigure(0, weight=1)
        self.status_label = tk.Label(bar, textvariable=self.var_status, bg=Palette.BACKGROUND_HIGH,
                                     fg=Palette.TEXT_SOFT, font=(Palette.FONT, 9), anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew", padx=16, pady=6)
        tk.Label(bar, text="Python + Tkinter  ·  única importación: import tkinter as tk",
                 bg=Palette.BACKGROUND_HIGH, fg=Palette.TEXT_DIM,
                 font=(Palette.FONT, 8)).grid(row=0, column=1, padx=16)

    # ------------------------------------------------------------------ clock drawing
    def _draw_dial(self, _event=None):
        """Redraws the whole dial (called when the window is created and when it is resized)."""
        canvas = self.clock_canvas
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 80 or height < 80:
            return
        cx = width / 2.0
        cy = height / 2.0
        r = min(width, height) / 2.0 - 22
        self._clock_geometry = (cx, cy, r)
        point = ArcaneMath.point_on_circle

        # Halo and decorative borders
        for halo_width, color in ((20, "#0f1d36"), (13, "#13254a"), (7, "#183060")):
            canvas.create_oval(cx - r - halo_width, cy - r - halo_width,
                               cx + r + halo_width, cy + r + halo_width, outline=color, width=3)
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=Palette.DIAL_RING,
                           outline=Palette.GOLD, width=3)
        canvas.create_oval(cx - r + 7, cy - r + 7, cx + r - 7, cy + r - 7, fill=Palette.DIAL,
                           outline=Palette.TURQUOISE_DARK, width=1)
        canvas.create_oval(cx - r * 0.56, cy - r * 0.56, cx + r * 0.56, cy + r * 0.56,
                           outline="#14284a", width=1)
        canvas.create_oval(cx - r * 0.3, cy - r * 0.3, cx + r * 0.3, cy + r * 0.3,
                           outline="#14284a", width=1, dash=(2, 4))

        # Decorative diamonds at the cardinal points, outside the ring
        for angle in (0, 90, 180, 270):
            px, py = point(cx, cy, r + 12, angle)
            canvas.create_polygon(px, py - 4, px + 4, py, px, py + 4, px - 4, py,
                                  fill=Palette.GOLD, outline="")

        # Minute marks (60) and hour marks (every 5)
        for mark in range(60):
            angle = mark * 6
            if mark % 5 == 0:
                x1, y1 = point(cx, cy, r * 0.82, angle)
                x2, y2 = point(cx, cy, r * 0.93, angle)
                canvas.create_line(x1, y1, x2, y2, fill=Palette.GOLD, width=max(3, int(r * 0.02)),
                                   capstyle="round")
            else:
                x1, y1 = point(cx, cy, r * 0.885, angle)
                x2, y2 = point(cx, cy, r * 0.93, angle)
                canvas.create_line(x1, y1, x2, y2, fill=Palette.TEXT_DIM, width=1)

        # Numbers: obtained by TRAVERSING the circular doubly linked list
        font_size = max(11, int(r * 0.12))
        for value in self.hour_list.traverse_forward():
            x, y = point(cx, cy, r * 0.69, value * 30)
            canvas.create_text(x, y, text=str(value), fill=Palette.TEXT,
                               font=(Palette.FONT, font_size, "bold"),
                               tags=("number", "number_{}".format(value)))

        # Dial labels
        canvas.create_text(cx, cy - r * 0.36, text="A R C A N O", fill=Palette.GOLD,
                           font=(Palette.FONT, max(8, int(r * 0.055)), "bold"))
        canvas.create_text(cx, cy - r * 0.27, text="lista circular doble", fill=Palette.TEXT_DIM,
                           font=(Palette.FONT, max(7, int(r * 0.038))))
        canvas.create_text(cx, cy + r * 0.33, text="", fill=Palette.TURQUOISE,
                           font=(Palette.MONO, max(9, int(r * 0.065)), "bold"), tags="dial_period")

        # Hands (created once; afterwards they are only moved with coords)
        canvas.create_line(0, 0, 0, 0, fill="#050b16", width=max(6, int(r * 0.05)),
                           capstyle="round", tags="hour_shadow")
        canvas.create_line(0, 0, 0, 0, fill=Palette.GOLD, width=max(5, int(r * 0.045)),
                           capstyle="round", tags="hour_hand")
        canvas.create_line(0, 0, 0, 0, fill="#050b16", width=max(4, int(r * 0.032)),
                           capstyle="round", tags="minute_shadow")
        canvas.create_line(0, 0, 0, 0, fill=Palette.TEXT, width=max(3, int(r * 0.028)),
                           capstyle="round", tags="minute_hand")
        canvas.create_line(0, 0, 0, 0, fill=Palette.TURQUOISE, width=2, capstyle="round",
                           tags="second_hand")
        canvas.create_oval(0, 0, 0, 0, fill=Palette.TURQUOISE, outline="", tags="counterweight")

        # Center
        rc = max(6, r * 0.05)
        canvas.create_oval(cx - rc, cy - rc, cx + rc, cy + rc, fill=Palette.GOLD, outline=Palette.DIAL, width=2)
        canvas.create_oval(cx - rc * 0.45, cy - rc * 0.45, cx + rc * 0.45, cy + rc * 0.45,
                           fill=Palette.TURQUOISE, outline="")

        self._update_hands()

    def _update_hands(self):
        """Moves the hands according to the current time using the angles from ArcaneTime."""
        if self._clock_geometry is None:
            return
        cx, cy, r = self._clock_geometry
        canvas = self.clock_canvas
        point = ArcaneMath.point_on_circle
        hour_angle, minute_angle, second_angle = self.time.angles()

        def place(tag, angle, length, tail, offset=0):
            x1, y1 = point(cx, cy, tail, angle + 180)
            x2, y2 = point(cx, cy, length, angle)
            canvas.coords(tag, x1 + offset, y1 + offset, x2 + offset, y2 + offset)

        place("hour_shadow", hour_angle, r * 0.48, r * 0.08, 2)
        place("hour_hand", hour_angle, r * 0.48, r * 0.08)
        place("minute_shadow", minute_angle, r * 0.72, r * 0.1, 2)
        place("minute_hand", minute_angle, r * 0.72, r * 0.1)
        place("second_hand", second_angle, r * 0.86, r * 0.2)
        px, py = point(cx, cy, r * 0.16, second_angle + 180)
        rp = max(3, r * 0.025)
        canvas.coords("counterweight", px - rp, py - rp, px + rp, py + rp)
        canvas.tag_raise("second_hand")
        canvas.tag_raise("counterweight")

        canvas.itemconfigure("number", fill=Palette.TEXT)
        canvas.itemconfigure("number_{}".format(self.time.hour), fill=Palette.TURQUOISE)
        canvas.itemconfigure("dial_period", text=self.time.period())

    # ------------------------------------------------------------------ list drawing
    def _draw_list(self, _event=None):
        """Draws the diagram following the REAL references of each node."""
        canvas = self.list_canvas
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 80 or height < 80 or self.hour_list.is_empty():
            return
        cx = width / 2.0
        cy = height / 2.0
        radius = min(width, height) / 2.0 - 20
        node_radius = max(10, min(24, radius * 0.15))
        size = self.hour_list.get_size()

        positions = {}
        node = self.hour_list.head
        for _ in range(size):
            positions[node] = ArcaneMath.point_on_circle(cx, cy, radius, node.value * 30)
            node = node.next

        # Links: turquoise arrow = next, gold arrow = prev
        node = self.hour_list.head
        for _ in range(size):
            self._draw_link(positions[node], positions[node.next], node_radius, Palette.TURQUOISE)
            self._draw_link(positions[node], positions[node.prev], node_radius, Palette.GOLD)
            node = node.next

        # Nodes
        current = self.time.hour_node
        font = (Palette.FONT, max(8, int(node_radius * 0.75)), "bold")
        node = self.hour_list.head
        for _ in range(size):
            x, y = positions[node]
            fill, outline, text_color, thickness = Palette.BUTTON, Palette.TURQUOISE_DARK, Palette.TEXT, 1
            if node is current:
                fill, outline, text_color, thickness = Palette.TURQUOISE, Palette.TURQUOISE, Palette.BACKGROUND, 2
            if node.value == self._traversal_node:
                outline, thickness = Palette.GOLD, 3
                if node is not current:
                    fill, text_color = Palette.GOLD_DARK, "#ffffff"
            canvas.create_oval(x - node_radius, y - node_radius, x + node_radius, y + node_radius,
                               fill=fill, outline=outline, width=thickness)
            canvas.create_text(x, y, text=str(node.value), fill=text_color, font=font)
            node = node.next

        # Center information
        tail = self.hour_list.get_tail()
        canvas.create_text(cx, cy - 22, text="cabeza → {}".format(self.hour_list.head.value),
                           fill=Palette.TEXT_SOFT, font=(Palette.MONO, 9))
        canvas.create_text(cx, cy - 6, text="cola → {}".format(tail.value),
                           fill=Palette.TEXT_SOFT, font=(Palette.MONO, 9))
        canvas.create_text(cx, cy + 12, text="tamaño = {}".format(size),
                           fill=Palette.GOLD, font=(Palette.MONO, 10, "bold"))
        canvas.create_text(cx, cy + 28, text="actual = {}".format(current.value),
                           fill=Palette.TURQUOISE, font=(Palette.MONO, 10, "bold"))

    def _draw_link(self, origin, target, node_radius, color):
        """Arrow shifted to the right of its direction so that 'next' and 'prev' do not overlap."""
        x1, y1 = origin
        x2, y2 = target
        dx = x2 - x1
        dy = y2 - y1
        length = ArcaneMath.square_root(dx * dx + dy * dy)
        if length == 0:
            return
        ux, uy = dx / length, dy / length
        nx, ny = -uy, ux
        gap = max(2.5, node_radius * 0.28)
        start_x = x1 + ux * (node_radius * 0.75) + nx * gap
        start_y = y1 + uy * (node_radius * 0.75) + ny * gap
        end_x = x2 - ux * (node_radius * 0.95) + nx * gap
        end_y = y2 - uy * (node_radius * 0.95) + ny * gap
        self.list_canvas.create_line(start_x, start_y, end_x, end_y, fill=color, width=1.6,
                                     arrow="last", arrowshape=(6, 7, 3))

    def _update_node_text(self):
        node = self.time.hour_node
        self.var_node.set("anterior {:>2}  ←  [ {:>2} ]  →  siguiente {:>2}".format(
            node.prev.value, node.value, node.next.value))

    # ------------------------------------------------------------------ clock loop
    def _system_milliseconds(self):
        """Milliseconds since the Unix epoch, using Tcl's 'clock' command included in Tkinter."""
        return int(self.root.tk.call("clock", "milliseconds"))

    def _local_time(self, milliseconds):
        """Converts milliseconds to (hour_24, minutes, seconds) using Colombia's time zone (UTC-5)."""
        text = self.root.tk.call("clock", "format", milliseconds // 1000, "-format", "%H %M %S",
                                 "-timezone", "-0500")
        parts = str(text).split()
        return int(parts[0]), int(parts[1]), int(parts[2])

    def _system_time_text(self):
        hours, minutes, seconds = self._local_time(self._system_milliseconds())
        return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

    def _clock_loop(self):
        """
        Runs every 100 ms with after(). It accumulates the real elapsed time and,
        for every full 1000 ms, adds one second to ArcaneTime. No infinite loops are used.
        """
        now = self._system_milliseconds()
        if not self.paused:
            if self._last_ms is not None:
                self._accumulated_ms += max(0, now - self._last_ms)
            changed = False
            while self._accumulated_ms >= 1000:
                self._accumulated_ms -= 1000
                self.time.add_second()
                changed = True
            if changed:
                self._refresh_time_view()
        self._last_ms = now

        self._pulse_counter += 1
        if self._pulse_counter % 5 == 0:
            self._pulse()
        self._clock_loop_id = self.root.after(self.CLOCK_INTERVAL_MS, self._clock_loop)

    def _pulse(self):
        """Makes the header's running indicator blink."""
        if self.paused:
            color = Palette.WARNING
        else:
            color = Palette.SUCCESS if (self._pulse_counter // 5) % 2 == 0 else Palette.TURQUOISE_DARK
        self.pulse_canvas.itemconfigure("pulse", fill=color)

    def _refresh_time_view(self):
        """Refreshes the digital time, the hands and, if the hour changed, the list diagram."""
        self.var_digital_time.set(self.time.text_12h())
        self.var_period.set(self.time.period())
        self.var_time_detail.set("24 h: {}  ·  nodo actual: {}".format(
            self.time.text_24h(), self.time.hour))
        self._update_hands()
        if self._drawn_hour is not self.time.hour_node:
            self._drawn_hour = self.time.hour_node
            self._draw_list()
            self._update_node_text()

    # ------------------------------------------------------------------ time actions
    def sync_with_system(self, announce=True):
        """Takes the local system time and loads it by finding its node in the list."""
        milliseconds = self._system_milliseconds()
        hours, minutes, seconds = self._local_time(milliseconds)
        self.time.set_time(hours, minutes, seconds)
        self._accumulated_ms = milliseconds % 1000
        self._last_ms = milliseconds
        self._refresh_time_view()
        if announce:
            self.show_status("Hora sincronizada con el sistema: {} {} (nodo {} encontrado con find()).".format(
                self.time.text_12h(), self.time.period(), self.time.hour), "success")

    def pause_clock(self):
        if self.paused:
            self.show_status("El reloj ya está en pausa.", "warning")
            return
        self.paused = True
        self.pause_button.set_enabled(False)
        self.resume_button.set_enabled(True)
        self.var_indicator.set("EN PAUSA")
        self.indicator_label.configure(fg=Palette.WARNING)
        self.pulse_canvas.itemconfigure("pulse", fill=Palette.WARNING)
        self.show_status("Reloj en pausa en {} {}. Puedes ajustar la hora y luego reanudar.".format(
            self.time.text_12h(), self.time.period()), "warning")

    def resume_clock(self):
        if not self.paused:
            self.show_status("El reloj ya está en marcha.", "warning")
            return
        self.paused = False
        self._last_ms = self._system_milliseconds()
        self.pause_button.set_enabled(True)
        self.resume_button.set_enabled(False)
        self.var_indicator.set("EN MARCHA")
        self.indicator_label.configure(fg=Palette.SUCCESS)
        self.show_status("Reloj reanudado desde {} {}.".format(
            self.time.text_12h(), self.time.period()), "success")

    def _move_hour(self, forward, source):
        """Moves the hour one node using the list's move_forward() or move_backward()."""
        previous = self.time.hour
        if forward:
            self.time.next_hour()
            method, link = "move_forward({})".format(previous), "next"
        else:
            self.time.previous_hour()
            method, link = "move_backward({})".format(previous), "prev"
        self._refresh_time_view()
        new_hour = self.time.hour
        extra = ""
        if (forward and previous == 12) or (not forward and previous == 1):
            extra = "  ¡Se cruzó el enlace circular {} → {}!".format(previous, new_hour)
        self.show_status("{}: hour_list.{} siguió el enlace '{}' del nodo {} y llegó al nodo {}.{}".format(
            source, method, link, previous, new_hour, extra), "success" if extra else "info")

    def add_hour(self):
        self._move_hour(True, "+1 hora")

    def subtract_hour(self):
        self._move_hour(False, "−1 hora")

    def go_next_hour(self):
        self._move_hour(True, "Hora siguiente")

    def go_previous_hour(self):
        self._move_hour(False, "Hora anterior")

    def add_minute(self):
        previous_hour = self.time.hour
        self.time.add_minute()
        self._refresh_time_view()
        message = "+1 minuto → {} {}.".format(self.time.text_12h(), self.time.period())
        if self.time.hour != previous_hour:
            message += " Paso de 59 a 00: la hora avanzó del nodo {} al {}.".format(previous_hour, self.time.hour)
        self.show_status(message)

    def subtract_minute(self):
        previous_hour = self.time.hour
        self.time.subtract_minute()
        self._refresh_time_view()
        message = "−1 minuto → {} {}.".format(self.time.text_12h(), self.time.period())
        if self.time.hour != previous_hour:
            message += " Paso de 00 a 59: la hora retrocedió del nodo {} al {}.".format(previous_hour, self.time.hour)
        self.show_status(message)

    # ------------------------------------------------------------------ traversals and integrity
    def traverse_forward(self):
        values = self.hour_list.traverse_forward()
        self._start_animation(values + [values[0]], "→", "hacia adelante (enlaces 'next')")

    def traverse_backward(self):
        values = self.hour_list.traverse_backward()
        self._start_animation(values + [values[0]], "←", "hacia atrás (enlaces 'prev')")

    def _start_animation(self, sequence, arrow, description):
        self._cancel_animation()
        self.show_status("Recorriendo la lista {}…".format(description))
        self._animate_step(sequence, 0, arrow, description)

    def _animate_step(self, sequence, index, arrow, description):
        if index >= len(sequence):
            self._animation_id = None
            self._traversal_node = None
            self._draw_list()
            self.var_traversal.set("{}  ({} nodos; volvió al inicio: es circular)".format(
                (" " + arrow + " ").join(str(v) for v in sequence), len(sequence) - 1))
            self.show_status("Recorrido {} completado: se visitaron {} nodos y el enlace final "
                             "regresó al nodo {}.".format(description, len(sequence) - 1, sequence[0]),
                             "success")
            return
        self._traversal_node = sequence[index]
        self._draw_list()
        self.var_traversal.set((" " + arrow + " ").join(str(v) for v in sequence[:index + 1]))
        self._animation_id = self.root.after(self.ANIMATION_STEP_MS, self._animate_step,
                                             sequence, index + 1, arrow, description)

    def _cancel_animation(self):
        if self._animation_id is not None:
            self.root.after_cancel(self._animation_id)
            self._animation_id = None
        self._traversal_node = None

    def verify_integrity(self, announce=True):
        """Calls CircularDoublyLinkedList.verify_integrity() and shows the result."""
        is_valid, message = self.hour_list.verify_integrity()
        self._last_integrity = is_valid
        color = Palette.SUCCESS if is_valid else Palette.ERROR
        self.integrity_canvas.itemconfigure("dot", fill=color)
        self.integrity_label.configure(fg=color)
        if is_valid:
            self.var_integrity.set("Lista íntegra: enlaces coherentes y circulares")
        else:
            self.var_integrity.set("Error de integridad en la lista")
        self.var_size.set("Tamaño actual de la lista: {} nodos".format(self.hour_list.get_size()))
        self.last_check_label.configure(fg=color)
        self.var_last_check.set("Última verificación: {} ({})".format(
            "CORRECTA" if is_valid else "FALLIDA", self._system_time_text()))
        if announce:
            self.show_status("verify_integrity(): " + message, "success" if is_valid else "error")

    # ------------------------------------------------------------------ stopwatch
    def start_stopwatch(self):
        if not self.stopwatch.start():
            self.show_status("El cronómetro ya está en marcha; no se inicia un segundo ciclo.", "warning")
            return
        if self._stopwatch_loop_id is None:
            self._stopwatch_loop()
        self._refresh_stopwatch_view()
        self.show_status("Cronómetro iniciado.", "success")

    def pause_stopwatch(self):
        if not self.stopwatch.pause():
            self.show_status("El cronómetro no está en marcha.", "warning")
            return
        self._stop_stopwatch_loop()
        self._refresh_stopwatch_view()
        self.show_status("Cronómetro en pausa en {}.".format(self.stopwatch.text()), "warning")

    def reset_stopwatch(self):
        self._stop_stopwatch_loop()
        self.stopwatch.reset()
        self._refresh_stopwatch_view()
        self.show_status("Cronómetro reiniciado a 00:00:00.")

    def _stopwatch_loop(self):
        self._stopwatch_loop_id = None
        self._refresh_stopwatch_view()
        if self.stopwatch.running:
            self._stopwatch_loop_id = self.root.after(self.STOPWATCH_INTERVAL_MS, self._stopwatch_loop)

    def _stop_stopwatch_loop(self):
        if self._stopwatch_loop_id is not None:
            self.root.after_cancel(self._stopwatch_loop_id)
            self._stopwatch_loop_id = None

    def _refresh_stopwatch_view(self):
        self.var_stopwatch.set(self.stopwatch.text())
        self.var_tenths.set(".{}".format(self.stopwatch.tenths()))
        running = self.stopwatch.running
        has_time = self.stopwatch.elapsed_ms() > 0
        if running:
            self.var_stopwatch_state.set("● En marcha")
            self.stopwatch_state_label.configure(fg=Palette.SUCCESS)
        elif has_time:
            self.var_stopwatch_state.set("En pausa")
            self.stopwatch_state_label.configure(fg=Palette.WARNING)
        else:
            self.var_stopwatch_state.set("Detenido")
            self.stopwatch_state_label.configure(fg=Palette.TEXT_DIM)
        self.stopwatch_start_button.set_enabled(not running)
        self.stopwatch_pause_button.set_enabled(running)
        self.stopwatch_reset_button.set_enabled(running or has_time)

    # ------------------------------------------------------------------ self-tests
    def show_self_tests(self):
        """Runs run_self_tests() and shows the result in a window."""
        results = run_self_tests()
        passed = sum(1 for _, ok, _ in results if ok)
        total = len(results)

        window = tk.Toplevel(self.root)
        window.title("Autopruebas — Reloj Arcano")
        window.configure(bg=Palette.BACKGROUND)
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - 640) // 2)
        y = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - 520) // 2)
        window.geometry("640x520+{}+{}".format(x, y))
        window.transient(self.root)
        color = Palette.SUCCESS if passed == total else Palette.ERROR
        tk.Label(window, text="Autopruebas: {} de {} aprobadas".format(passed, total),
                 bg=Palette.BACKGROUND, fg=color, font=(Palette.FONT, 13, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        frame = tk.Frame(window, bg=Palette.PANEL)
        frame.pack(fill="both", expand=True, padx=16)
        text_box = tk.Text(frame, bg=Palette.PANEL, fg=Palette.TEXT, font=(Palette.MONO, 9), relief="flat",
                           bd=0, padx=10, pady=8, wrap="word", highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, command=text_box.yview)
        text_box.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text_box.pack(side="left", fill="both", expand=True)
        text_box.tag_configure("ok", foreground=Palette.SUCCESS)
        text_box.tag_configure("fail", foreground=Palette.ERROR)
        text_box.tag_configure("detail", foreground=Palette.TEXT_SOFT)
        for number, (name, ok, detail) in enumerate(results, start=1):
            text_box.insert("end", "[{}] ".format("OK" if ok else "FALLO"), "ok" if ok else "fail")
            text_box.insert("end", "{:02d}. {}\n".format(number, name))
            if detail:
                text_box.insert("end", "      " + detail + "\n", "detail")
        text_box.configure(state="disabled")
        ArcaneButton(window, "Cerrar", window.destroy, "primary").pack(anchor="e", padx=16, pady=12)
        self.show_status("Autopruebas ejecutadas: {} de {} aprobadas.".format(passed, total),
                         "success" if passed == total else "error")

    # ------------------------------------------------------------------ utilities
    def show_status(self, message, kind="info"):
        """Shows a message in the bottom bar together with the system time."""
        colors = {"info": Palette.TEXT_SOFT, "success": Palette.SUCCESS,
                  "warning": Palette.WARNING, "error": Palette.ERROR}
        self.var_status.set("[{}]  {}".format(self._system_time_text(), message))
        self.status_label.configure(fg=colors.get(kind, Palette.TEXT_SOFT))

    def _report_error(self, error_type, value, _traceback):
        """Shows any unexpected error raised by an event in the status bar."""
        self.show_status("Error inesperado ({}): {}".format(error_type.__name__, value), "error")

    def close(self):
        """Cancels the scheduled loops and closes the window."""
        for identifier in (self._clock_loop_id, self._stopwatch_loop_id, self._animation_id):
            if identifier is not None:
                try:
                    self.root.after_cancel(identifier)
                except tk.TclError:
                    pass
        self.root.destroy()


# =====================================================================================
# 8. LOGIC SELF-TESTS (no window needed)
# =====================================================================================
class _FakeClock:
    """Controllable millisecond source used to test the stopwatch."""

    def __init__(self):
        self.ms = 0

    def __call__(self):
        return self.ms


def run_self_tests():
    """
    Runs tests for the list, the time, the math and the stopwatch.
    Returns [(name, ok, detail)]. Names and details are shown in the
    interface, so they are written in Spanish.
    """
    results = []

    def check(name, condition, detail=""):
        results.append((name, bool(condition), detail))

    hour_list = CircularDoublyLinkedList.create_clock_hours()

    # --- Circular doubly linked list ---
    check("La lista contiene exactamente 12 nodos",
          hour_list.get_size() == 12, "get_size() = {}".format(hour_list.get_size()))
    forward = hour_list.traverse_forward()
    check("Recorrido hacia adelante = 1..12", forward == list(range(1, 13)), str(forward))
    backward = hour_list.traverse_backward()
    check("Recorrido hacia atrás = 12..1", backward == list(range(12, 0, -1)), str(backward))
    check("move_forward(12) devuelve el nodo 1", hour_list.move_forward(12).value == 1)
    check("move_backward(1) devuelve el nodo 12", hour_list.move_backward(1).value == 12)
    check("12.next es el mismo objeto que la cabeza (1)", hour_list.find(12).next is hour_list.head)
    check("1.prev es el mismo objeto que la cola (12)", hour_list.head.prev is hour_list.find(12))
    consistent = True
    node = hour_list.head
    for _ in range(hour_list.get_size()):
        if node.next.prev is not node or node.prev.next is not node:
            consistent = False
        node = node.next
    check("Todos los enlaces prev/next son coherentes", consistent)
    node = hour_list.head
    no_nulls = True
    for _ in range(36):                         # three full laps without finding None
        if node is None:
            no_nulls = False
            break
        node = node.next
    check("Tres vueltas seguidas sin encontrar None", no_nulls and node is hour_list.head)
    is_valid, message = hour_list.verify_integrity()
    check("verify_integrity() aprueba la lista correcta", is_valid, message)
    check("find(7) encuentra el nodo 7", hour_list.find(7) is not None and hour_list.find(7).value == 7)
    check("find(13) devuelve None", hour_list.find(13) is None)
    try:
        hour_list.append(5)
        rejected = False
    except ValueError:
        rejected = True
    check("append() rechaza una hora repetida", rejected and hour_list.get_size() == 12)
    broken = CircularDoublyLinkedList.create_clock_hours()
    broken.find(6).prev = broken.find(3)        # a link is damaged on purpose
    broken_valid, broken_message = broken.verify_integrity()
    check("verify_integrity() detecta un enlace dañado", not broken_valid, broken_message)

    # --- Time ---
    time = ArcaneTime(hour_list)
    time.set_time(23, 59, 59)
    time.add_second()
    check("23:59:59 + 1 s = 00:00:00 (12:00:00 AM)",
          time.text_24h() == "00:00:00" and time.text_12h() == "12:00:00" and time.period() == "AM",
          "{} {}".format(time.text_12h(), time.period()))
    time.set_time(0, 0, 30)
    time.subtract_minute()
    check("12:00 AM − 1 min = 11:59 PM", time.text_24h() == "23:59:30", time.text_24h())
    time.set_time(11, 59, 0)
    time.add_minute()
    check("11:59 AM + 1 min = 12:00 PM", time.text_24h() == "12:00:00" and time.period() == "PM",
          "{} {}".format(time.text_12h(), time.period()))
    time.set_time(12, 30, 0)
    time.next_hour()
    check("+1 hora desde las 12 llega a la 1 (enlace circular)", time.hour == 1 and time.text_24h() == "13:30:00",
          time.text_24h())
    time.previous_hour()
    check("−1 hora desde la 1 llega a las 12 (enlace circular)", time.hour == 12, str(time.hour))
    check("La hora del reloj es un objeto HourNode de la lista",
          isinstance(time.hour_node, HourNode) and hour_list.find(time.hour) is time.hour_node)

    # --- Math and hands ---
    m = ArcaneMath
    check("sen(30°) = 0.5", abs(m.sine(m.degrees_to_radians(30)) - 0.5) < 1e-9)
    check("cos(60°) = 0.5", abs(m.cosine(m.degrees_to_radians(60)) - 0.5) < 1e-9)
    check("sen(1000°) = sen(280°)",
          abs(m.sine(m.degrees_to_radians(1000)) - m.sine(m.degrees_to_radians(280))) < 1e-9)
    check("raíz cuadrada de 2", abs(m.square_root(2) - 1.4142135623730951) < 1e-9)
    expected = {3: (100, 0), 6: (0, 100), 9: (-100, 0), 12: (0, -100)}
    for hour, (ex, ey) in expected.items():
        time.set_time(hour % 12 if hour != 12 else 12, 0, 0)
        hour_angle = time.angles()[0]
        x, y = m.point_on_circle(0, 0, 100, hour_angle)
        check("A las {}:00 la manecilla horaria apunta al {}".format(hour, hour),
              abs(x - ex) < 1e-6 and abs(y - ey) < 1e-6,
              "ángulo={}°, punta=({:.2f}, {:.2f})".format(hour_angle, x, y))
    time.set_time(3, 30, 0)
    check("A las 3:30 la horaria está a mitad entre 3 y 4 (105°)", abs(time.angles()[0] - 105) < 1e-9)
    time.set_time(10, 15, 30)
    check("A los 15 min 30 s la minutera está en 93°", abs(time.angles()[1] - 93) < 1e-9)

    # --- Stopwatch ---
    source = _FakeClock()
    stopwatch = Stopwatch(source)
    check("El cronómetro empieza en 00:00:00", stopwatch.text() == "00:00:00")
    stopwatch.start()
    source.ms = 1500
    second_start = stopwatch.start()
    source.ms = 3725000
    check("Un segundo 'Iniciar' no crea otro conteo", second_start is False)
    check("Mide 01:02:05 tras 3 725 000 ms", stopwatch.text() == "01:02:05", stopwatch.text())
    stopwatch.pause()
    source.ms = 9999999
    check("En pausa el tiempo no avanza", stopwatch.text() == "01:02:05", stopwatch.text())
    stopwatch.reset()
    check("Reiniciar vuelve a 00:00:00 y lo detiene", stopwatch.text() == "00:00:00" and not stopwatch.running)

    return results


# =====================================================================================
# ENTRY POINT
# =====================================================================================
def main():
    root = tk.Tk()
    ArcaneClock(root)
    root.mainloop()


if __name__ == "__main__":
    main()
