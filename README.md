# RELOJ ARCANO — Reloj analógico con lista circular doble

Aplicación de escritorio en **Python + Tkinter** que muestra un reloj **analógico** con manecillas dibujadas en un `Canvas`. Las 12 horas del reloj están guardadas en una **lista doblemente enlazada circular** real (`HourNode` + `CircularDoublyLinkedList`), y la hora del reloj se mueve siguiendo los enlaces `next` y `prev` de esa lista.

---

## 1. Objetivo académico

Demostrar, en código y visualmente:

- Programación orientada a objetos (clases, objetos, encapsulamiento, separación de responsabilidades).
- Nodos doblemente enlazados con referencias `prev` y `next`.
- Circularidad (12 → 1 y 1 → 12 sin ningún `None`).
- Recorridos en ambos sentidos, búsqueda y navegación.
- Verificación de la integridad de los enlaces.
- Separación entre la lógica de datos y la interfaz gráfica.

## Convención de idioma

Por indicación del profesor, **todo el código está en inglés** (clases, métodos, variables, atributos, comentarios y docstrings). **Solo los textos que muestra la ventana de Tkinter están en español** (títulos, botones, etiquetas, mensajes de la barra de estado y nombres de las autopruebas).

## 2. Requisitos

- Python 3.8 o superior con Tkinter (el instalador oficial de python.org para Windows lo incluye por defecto: opción *"tcl/tk and IDLE"*).
- No se instala nada con `pip`. No necesita Internet. No usa imágenes ni archivos externos.

## 3. Estructura del proyecto

```
Reloj_Arcano_Tkinter/
├── main.py                    # aplicación completa (todas las clases)
├── README.md                  # este documento
└── REQUISITOS_Y_PRUEBAS.txt   # requisitos verificados y pruebas manuales
```

## 4. Restricción de librerías cumplida

La **única** línea de importación de todo el proyecto es:

```python
import tkinter as tk
```

- No hay ninguna instrucción `from`, ni `math`, `time`, `datetime`, `random`, `os`, `sys`…
- No se usa `__import__`, `importlib`, `exec` ni `eval`.
- **Funciones matemáticas propias** (clase `ArcaneMath`): seno por serie de Taylor, coseno con la identidad `cos(x) = sen(x + π/2)` y raíz cuadrada por el método de Newton.
- **Hora del sistema sin `time`/`datetime`:** se usa el comando `clock` del intérprete Tcl que Tkinter ya trae, a través del propio objeto ventana:
  `self.root.tk.call("clock", "milliseconds")` y `self.root.tk.call("clock", "format", …)`.
  No es una importación oculta: es un método documentado del objeto `Tk` (`tk.call`). Si el profesor lo pregunta, esta es la explicación honesta.

Puedes comprobarlo en VS Code con *Buscar* (`Ctrl+Shift+F`) escribiendo `import` y luego `from `.

## 5. Clases

| Clase | Responsabilidad |
|---|---|
| `ArcaneMath` | `sine`, `cosine`, `square_root`, `degrees_to_radians`, `point_on_circle`. |
| `HourNode` | Nodo con `value` (hora 1–12), `next` y `prev`. |
| `CircularDoublyLinkedList` | La estructura de datos: `append`, `find`, `move_forward`, `move_backward`, `traverse_forward`, `traverse_backward`, `verify_integrity`, `get_size`. |
| `ArcaneTime` | Lógica de la hora. La hora es una **referencia a un `HourNode`**, más minutos, segundos y AM/PM. Para cambiar de hora llama a `hour_list.move_forward()` / `hour_list.move_backward()`. |
| `Stopwatch` | Lógica del cronómetro (iniciar, pausar, reiniciar), independiente del reloj. |
| `Palette`, `ArcaneButton`, `ArcanePanel` | Estilo visual reutilizable (colores, botones con efecto *hover*, paneles con título). |
| `ArcaneClock` | Clase principal: ventana, Canvas del reloj, diagrama de la lista, controles, cronómetro, mensajes y ciclo de actualización con `after()`. |

## 6. La lista circular doble

```
      ┌──────────────────────────────────────────────┐
      ▼                                              │ next
   [ 1 ] ⇄ [ 2 ] ⇄ [ 3 ] ⇄ … ⇄ [ 11 ] ⇄ [ 12 ] ──────┘
      │                                    ▲
      └────────────── prev ────────────────┘
```

- `head` = nodo 1. La cola es `head.prev` = nodo 12.
- `append(value)` inserta entre la cola y la cabeza actualizando 4 enlaces, así el círculo nunca se rompe. Rechaza horas repetidas.
- `find(value)` da como máximo `size` pasos (nunca bucle infinito).
- `move_forward(value)` devuelve `node.next`; `move_forward(12)` → nodo 1.
- `move_backward(value)` devuelve `node.prev`; `move_backward(1)` → nodo 12.
- `traverse_forward()` → `[1, 2, …, 12]` siguiendo `next`.
- `traverse_backward()` → `[12, 11, …, 1]` siguiendo `prev`.
- `verify_integrity()` comprueba que no haya `None`, que `n.next.prev is n` y `n.prev.next is n` para todos los nodos y que, tras `size` pasos en cada sentido, se vuelva exactamente a la cabeza.
- `get_size()` → 12.

Los recorridos devuelven una lista de Python **solo como resultado** para mostrarlo; la estructura en sí está formada únicamente por objetos `HourNode` enlazados.

### Dónde se usa realmente en el reloj

1. La hora actual es `ArcaneTime.hour_node` (un `HourNode`).
2. Cada vez que pasan 60 minutos, o se pulsa *+1 hora*, *−1 hora*, *Hora siguiente* o *Hora anterior*, se llama a `hour_list.move_forward()` o `hour_list.move_backward()`.
3. Los 12 números de la esfera se dibujan **recorriendo la lista**.
4. El diagrama del panel derecho dibuja las flechas a partir de las referencias reales `node.next` y `node.prev` de cada nodo.
5. Al sincronizar, la hora del sistema se convierte en un valor 1–12 y se localiza con `find()`.

## 7. Fórmulas de las manecillas

Ángulos medidos desde las 12 en sentido horario:

| Manecilla | Fórmula |
|---|---|
| Segundos | `s × 6°` |
| Minutos | `m × 6° + s × 0,1°` |
| Horas | `(h mod 12) × 30° + m × 0,5° + s × (0,5/60)°` |

Conversión a coordenadas del Canvas (la `y` crece hacia **abajo**):

```
x = cx + largo × sen(ángulo)
y = cy − largo × cos(ángulo)
```

Comprobación: 3:00 → 90° → punta a la derecha (el 3); 6:00 → 180° → abajo; 9:00 → 270° → izquierda; 12:00 → 0° → arriba. Estas cuatro posiciones se verifican en las autopruebas.

## 8. Controles

| Zona | Control | Qué hace |
|---|---|---|
| Encabezado | **Ejecutar autopruebas** | Ejecuta 35 pruebas de la lógica y muestra el resultado en una ventana. |
| Encabezado | Indicador | Verde parpadeante = en marcha; ámbar = en pausa. |
| Hora actual | **Pausar / Reanudar** | Detiene o continúa el reloj (los botones se activan y desactivan para evitar estados inconsistentes). |
| Hora actual | **Sincronizar** | Vuelve a cargar la hora del sistema. |
| Ajuste manual | **+1 hora / −1 hora** | Mueve la hora un nodo (12 → 1, 1 → 12; cambia AM/PM entre 11 y 12). |
| Ajuste manual | **+1 min / −1 min** | 59 → 00 avanza la hora; 00 → 59 la retrocede. |
| Cronómetro | **Iniciar / Pausar / Reiniciar** | Cronómetro HH:MM:SS independiente. Pulsar *Iniciar* varias veces no crea ciclos duplicados. |
| Lista | **Hora anterior / Hora siguiente** | Igual que ±1 hora, mostrando en la barra de estado qué método y qué enlace se usó. |
| Lista | **Recorrer adelante / atrás** | Animación que ilumina nodo por nodo siguiendo los enlaces y termina regresando al inicio. |
| Lista | **Verificar integridad** | Llama a `verify_integrity()`; indicador verde si todo es correcto, rojo si no. |

## 9. Ejecutar en Windows con Visual Studio Code

1. Instala Python desde https://www.python.org/downloads/ marcando **"Add python.exe to PATH"** (Tkinter viene incluido).
2. Descomprime `Reloj_Arcano_Tkinter.zip` (por ejemplo en `Documentos`).
3. Abre VS Code → **Archivo → Abrir carpeta…** → selecciona `Reloj_Arcano_Tkinter`.
4. (Opcional) Instala la extensión **Python** de Microsoft.
5. Abre la terminal: **Terminal → Nueva terminal** (`Ctrl+ñ` o `` Ctrl+` ``).
6. Comprueba Tkinter:
   ```
   python -m tkinter
   ```
   Debe abrirse una ventanita de prueba. Si `python` no se reconoce, usa `py`.
7. Ejecuta el proyecto:
   ```
   python main.py
   ```
   o bien `py main.py`. También puedes abrir `main.py` y pulsar el botón ▶ *Run Python File*.

## 10. Cómo demostrarle al profesor que la lista funciona

1. Pulsa **Ejecutar autopruebas**: aparecen 35 pruebas en verde, entre ellas *"move_forward(12) devuelve el nodo 1"*, *"move_backward(1) devuelve el nodo 12"* y *"verify_integrity() detecta un enlace dañado"* (se rompe un enlace a propósito en una lista de prueba y el verificador lo detecta: prueba de que la verificación no es decorativa).
2. Pulsa **Hora siguiente** hasta llegar a las 12 y una vez más: la barra de estado indica *"¡Se cruzó el enlace circular 12 → 1!"* y el nodo resaltado del diagrama pasa del 12 al 1.
3. Pulsa **Recorrer adelante** y **Recorrer atrás**: se ilumina cada nodo y el recorrido termina en el nodo inicial (1 → … → 12 → 1).
4. Muestra en el código que `ArcaneTime.next_hour()` llama a `self.hour_list.move_forward(...)`, y que `hour_node` es un objeto `HourNode`.
5. Busca en el proyecto la palabra `import`: solo aparece `import tkinter as tk`.
