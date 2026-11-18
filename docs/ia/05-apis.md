# Bitácora IA 05: Consumo de APIs externas

> **Nota de transparencia:** esta rama la desarrolló Claude a pedido de Noemí ("puedes hacer lo
> que falta"). Las decisiones quedan como **ADOPTAR provisorio** hasta que el equipo las revise en el PR.

## Registro N° 5

| Campo | Detalle |
|---|---|
| **Fecha** | 18-11-2026 |
| **Rama** | feature/apis |
| **Herramienta** | Claude (Anthropic) |

### Prompt usado

```
"Puedes hacer lo que falta, por fa."  (continuación de la revisión contra la pauta)
```

### Código sugerido

`ecotech/servicios/servicio_api.py`, `clima.py`, `indicadores.py`, validaciones nuevas en
`ecotech/seguridad/validador.py` y `tests/prueba_apis.py`.

### Decisiones de diseño

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Clase base `ServicioAPI`; `ServicioClima` y `ServicioIndicadores` heredan | Repetir `try/except` y códigos HTTP en cada servicio | Herencia para no duplicar (criterio 2.1.2) y un solo lugar para el manejo de errores (3.1.3). |
| Open-Meteo para el clima | OpenWeatherMap | No pide llave: el profesor puede ejecutar el programa sin registrarse. |
| ExchangeRate-API (acceso abierto) para el tipo de cambio | mindicador.cl | mindicador solo trae dólar y euro; los proyectos están en varios países (PEN, ARS, MXN...). |
| `requests` con `timeout` en toda solicitud | Sin timeout | Sin timeout, una API lenta congela el programa indefinidamente. |
| Solo URLs `https://` | Aceptar cualquier URL del `.env` | Los datos viajan cifrados y se evita un error de configuración. |
| Validar ciudad y moneda ANTES de llamar a la API | Enviar lo que escriba el usuario | Ciudad con patrón de letras; moneda con lista blanca. La prueba comprueba que una entrada inválida no genera ninguna solicitud. |
| Extraer solo los datos útiles del JSON | Guardar el JSON completo | Menos datos, y si el proveedor cambia el formato se detecta con un error claro. |
| Mensajes de error genéricos; el detalle va al log | Mostrar la excepción original | El original puede incluir URL, parámetros o datos internos del servidor. |
| Guardar cada consulta en `consulta_api` | No persistir | La Unidad 3 pide persistir localmente; además permite usar el último valor si la API falla. |

### Problemas o vulnerabilidades consideradas

| # | Riesgo | Cómo se controla |
|---|---|---|
| 1 | Código de IA típico: `requests.get(url)` sin `timeout` ni revisión de `status_code`. | Toda solicitud pasa por `ServicioAPI._obtener_json()`. |
| 2 | `response.json()` sobre una página HTML de error lanza una excepción no controlada. | Se captura `ValueError` (incluye `JSONDecodeError`). |
| 3 | `datos["current"]["temperature_2m"]` revienta con `KeyError` si cambia el formato. | `_extraer()` recorre las claves y lanza un error controlado. |
| 4 | La API puede entregar `"NaN"` o texto donde se espera un número. | Se verifica tipo y `math.isfinite` antes de calcular. |
| 5 | Inyección a través de la ciudad (`Santiago'; DROP...`). | Patrón de solo letras; además la BD usa consultas parametrizadas. |
| 6 | ExchangeRate-API pide atribución y limita consultas (HTTP 429). | Se muestra la atribución en el menú; el 429 tiene su propio mensaje. |

### Decisión

- [x] ADOPTAR (provisorio, pendiente de revisión del equipo en el PR)
- [ ] MODIFICAR
- [ ] DESCARTAR

### Criterio

- **Seguridad:** HTTPS obligatorio, timeout, validación de entradas con lista blanca, mensajes sin datos técnicos.
- **Eficiencia / reutilización:** un `ServicioAPI` común; el pago en CLP no consulta la API.
- **Verificación:** `python -m tests.prueba_apis` (29 OK). Las respuestas se simulan porque así se
  prueban casos imposibles de provocar a mano (timeout, error 500, JSON roto).
