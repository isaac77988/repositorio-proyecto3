"""
selector_fecha.py - Campo de fecha con mini calendario desplegable (solo tkinter).
"""
import calendar
import tkinter as tk
from datetime import date
from typing import Callable, Optional

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
DIAS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]


def _restar_anio(f: date, anios: int = 1) -> date:
    """Misma fecha hace `anios` años (29/feb pasa a 28/feb si no es bisiesto)."""
    try:
        return f.replace(year=f.year - anios)
    except ValueError:
        return f.replace(year=f.year - anios, day=28)


class SelectorFecha(tk.Frame):
    """Botón que muestra la fecha elegida y abre un calendario al pulsarlo."""

    def __init__(
        self,
        master,
        paleta: dict,
        inicial: Optional[date] = None,
        fecha_min: date = date(1990, 1, 1),
        fecha_max: Optional[date] = None,
        on_change: Optional[Callable[[date], None]] = None,
    ):
        super().__init__(master, bg=paleta["BG_APP"])
        self.p = paleta
        self.fecha_max = fecha_max or date.today()
        self.fecha_min = fecha_min
        self.on_change = on_change
        self._fecha = min(max(inicial or _restar_anio(self.fecha_max), fecha_min), self.fecha_max)
        self._popup: Optional[tk.Toplevel] = None
        self._mes_vista = self._fecha.replace(day=1)

        self._btn = tk.Button(
            self, text=self._texto_boton(), command=self.alternar,
            bg=paleta["BG_CARD"], fg=paleta["TEXTO_PRINCIPAL"],
            activebackground=paleta["BG_APP"], activeforeground=paleta["ACCESO_AZUL"],
            relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            font=("Segoe UI", 10), highlightthickness=1,
            highlightbackground=paleta["BORDE_SUTIL"],
        )
        self._btn.pack()

    # API pública

    def get(self) -> date:
        """Fecha actualmente seleccionada."""
        return self._fecha

    def set(self, fecha: date) -> None:
        """Cambia la fecha (se ajusta a los límites permitidos)."""
        self._fecha = min(max(fecha, self.fecha_min), self.fecha_max)
        self._btn.config(text=self._texto_boton())

    # Popup

    def _texto_boton(self) -> str:
        return f"\U0001F4C5  {self._fecha:%d/%m/%Y}"

    def alternar(self) -> None:
        if self._popup is not None:
            self._cerrar()
        else:
            self._abrir()

    def _abrir(self) -> None:
        p = self.p
        self._mes_vista = self._fecha.replace(day=1)
        w = tk.Toplevel(self)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=p["ACCESO_AZUL"])
        self._popup = w

        self._marco = tk.Frame(w, bg=p["BG_CARD"], padx=10, pady=10)
        self._marco.pack(padx=1, pady=1)
        self._dibujar()

        w.update_idletasks()
        x = self._btn.winfo_rootx()
        y = self._btn.winfo_rooty() + self._btn.winfo_height() + 4
        # Si no cabe debajo, se abre hacia arriba.
        if y + w.winfo_reqheight() > self.winfo_screenheight():
            y = self._btn.winfo_rooty() - w.winfo_reqheight() - 4
        w.geometry(f"+{x}+{max(y, 0)}")

        w.bind("<Escape>", lambda _e: self._cerrar())
        w.bind("<Button-1>", self._clic, add="+")
        try:
            w.focus_force()
            w.grab_set()
        except tk.TclError:
            pass

    def _clic(self, e) -> None:
        """Cierra el calendario si el clic cae fuera de él."""
        w = self._popup
        if w is None:
            return
        x0, y0 = w.winfo_rootx(), w.winfo_rooty()
        dentro = x0 <= e.x_root <= x0 + w.winfo_width() and y0 <= e.y_root <= y0 + w.winfo_height()
        if not dentro:
            self._cerrar()

    def _cerrar(self) -> None:
        w, self._popup = self._popup, None
        if w is not None:
            try:
                w.grab_release()
            except tk.TclError:
                pass
            w.destroy()

    # Dibujo del calendario

    def _estilo_nav(self, texto, comando, habilitado=True):
        p = self.p
        return tk.Button(
            self._cab, text=texto, command=comando, width=3,
            bg=p["BG_CARD"], fg=p["ACCESO_AZUL"], activebackground=p["BG_APP"],
            activeforeground=p["ACCESO_AZUL"], disabledforeground=p["BORDE_SUTIL"],
            relief="flat", bd=0, font=("Segoe UI", 10, "bold"), cursor="hand2",
            state="normal" if habilitado else "disabled",
        )

    def _mover(self, meses: int) -> None:
        total = self._mes_vista.year * 12 + (self._mes_vista.month - 1) + meses
        self._mes_vista = date(total // 12, total % 12 + 1, 1)
        self._dibujar()

    def _puede_mover(self, meses: int) -> bool:
        total = self._mes_vista.year * 12 + (self._mes_vista.month - 1) + meses
        destino = date(total // 12, total % 12 + 1, 1)
        ultimo = calendar.monthrange(destino.year, destino.month)[1]
        return destino.replace(day=ultimo) >= self.fecha_min and destino <= self.fecha_max

    def _dibujar(self) -> None:
        p = self.p
        for w in self._marco.winfo_children():
            w.destroy()

        self._cab = tk.Frame(self._marco, bg=p["BG_CARD"])
        self._cab.pack(fill="x", pady=(0, 6))
        self._estilo_nav("«", lambda: self._mover(-12), self._puede_mover(-12)).pack(side="left")
        self._estilo_nav("‹", lambda: self._mover(-1), self._puede_mover(-1)).pack(side="left")
        self._estilo_nav("»", lambda: self._mover(12), self._puede_mover(12)).pack(side="right")
        self._estilo_nav("›", lambda: self._mover(1), self._puede_mover(1)).pack(side="right")
        tk.Label(
            self._cab, text=f"{MESES[self._mes_vista.month - 1]} {self._mes_vista.year}",
            bg=p["BG_CARD"], fg=p["TEXTO_PRINCIPAL"], font=("Segoe UI", 10, "bold"),
        ).pack(side="left", expand=True)

        cuadro = tk.Frame(self._marco, bg=p["BG_CARD"])
        cuadro.pack()
        for col, d in enumerate(DIAS):
            tk.Label(cuadro, text=d, width=4, bg=p["BG_CARD"], fg=p["TEXTO_MUTED"],
                     font=("Segoe UI", 8, "bold")).grid(row=0, column=col, pady=(0, 2))

        hoy = date.today()
        semanas = calendar.Calendar(firstweekday=0).monthdayscalendar(
            self._mes_vista.year, self._mes_vista.month
        )
        for fila, semana in enumerate(semanas, start=1):
            for col, dia in enumerate(semana):
                if dia == 0:
                    continue
                f = date(self._mes_vista.year, self._mes_vista.month, dia)
                activo = self.fecha_min <= f <= self.fecha_max
                if f == self._fecha:
                    bg, fg = p["ACCESO_AZUL"], p["BTN_TEXTO"]
                else:
                    bg = p["BG_CARD"]
                    fg = p["TEXTO_PRINCIPAL"] if col < 5 else p["TEXTO_MUTED"]
                b = tk.Button(
                    cuadro, text=str(dia), width=4, bg=bg, fg=fg,
                    activebackground=p["ACCESO_AZUL"], activeforeground=p["BTN_TEXTO"],
                    disabledforeground=p["BORDE_SUTIL"], relief="flat", bd=0,
                    font=("Segoe UI", 9, "bold" if f == hoy else "normal"),
                    cursor="hand2" if activo else "arrow",
                    state="normal" if activo else "disabled",
                    command=lambda x=f: self._elegir(x),
                )
                if f == hoy:
                    b.config(highlightthickness=1, highlightbackground=p["VERDE_EXITO"])
                b.grid(row=fila, column=col, padx=1, pady=1)

        pie = tk.Frame(self._marco, bg=p["BG_CARD"])
        pie.pack(fill="x", pady=(8, 0))
        tk.Button(
            pie, text="Hoy", command=lambda: self._elegir(self.fecha_max),
            bg=p["BG_CARD"], fg=p["ACCESO_AZUL"], activebackground=p["BG_APP"],
            activeforeground=p["ACCESO_AZUL"], relief="flat", bd=0,
            font=("Segoe UI", 9, "bold"), cursor="hand2",
        ).pack(side="left")
        tk.Button(
            pie, text="Cerrar", command=self._cerrar,
            bg=p["BG_CARD"], fg=p["TEXTO_MUTED"], activebackground=p["BG_APP"],
            activeforeground=p["TEXTO_PRINCIPAL"], relief="flat", bd=0,
            font=("Segoe UI", 9), cursor="hand2",
        ).pack(side="right")

    def _elegir(self, f: date) -> None:
        self._fecha = f
        self._btn.config(text=self._texto_boton())
        self._cerrar()
        if self.on_change:
            self.on_change(f)

    def destroy(self) -> None:
        self._cerrar()
        super().destroy()
