# Bitácora IA 02: Implementación del modelo POO

> **Nota de transparencia:** en esta sesión el equipo delegó las decisiones de diseño en la IA
> por falta de tiempo ("adoptamos según lo que veas"). Todas las clases quedaron marcadas como
> `# IA: adoptado` de forma **provisoria**. Antes del merge a `develop`, el equipo debe revisar
> cada clase y, si cambia algo, actualizar aquí la decisión a MODIFICAR y el comentario del código
> a `# IA: modificado - <motivo>`.

---

## Registro N° 2

| Campo | Detalle |
|---|---|
| **Fecha** | 15-11-2026 |
| **Rama** | feature/modelo-poo |
| **Herramienta** | Claude Code (Anthropic) |

### Prompt usado

```
Eres mi compañero de programación en un proyecto universitario (INACAP, ramo POO Seguro).
El diagrama UML final es la fuente de verdad. Trabaja clase por clase.
Implementa en ecotech/modelos/: rol.py (Enum, el administrador es un rol), persona.py
(abstracta con @abstractmethod), empleado.py (super().__init__), gerente.py,
departamento.py (agregación 0..1 ◇ 0..* y → 1 Gerente), proyecto.py (N:N),
registro_tiempo.py (asociación, no composición), usuario.py (composición
Empleado 1 ◆ 0..1 Usuario, solo hash de contraseña).
En todas: atributos privados (__) con @property, setters con validación que lancen
ValueError o excepciones propias, __str__ legible, type hints. Respeta exactamente el UML;
si algo no calza, avísame. No escribas lógica de BD ni APIs.
Luego: docs/modelo-uml-vs-codigo.md y tests/prueba_modelo.py.
```

### Código sugerido

Archivos: `ecotech/excepciones.py`, `ecotech/modelos/_validaciones.py`, `rol.py`, `persona.py`,
`empleado.py`, `gerente.py`, `departamento.py`, `proyecto.py`, `registro_tiempo.py`,
`usuario.py` y `tests/prueba_modelo.py`. El detalle por clase está en la tabla de abajo y en
`docs/modelo-uml-vs-codigo.md`.

### Problemas o vulnerabilidades detectadas

| # | Clase | Problema detectado | Cómo se resolvió |
|---|---|---|---|
| 1 | Gerente | La primera versión declaraba `__departamento_a_cargo` como **atributo de clase** con valor `None` para no escribir `__init__`. Funciona, pero es confuso de defender y mezcla atributo de clase con atributo de instancia. | Se reescribió con `__init__` explícito que llama a `super().__init__(...)` e inicializa el atributo por instancia. |
| 2 | Empleado | El UML recibe `salario: double` en el constructor, pero no entrega el `ServicioCifrado` para cifrarlo. Guardarlo en texto plano contradice RNF02. | Se agregó el parámetro `cifrado` al constructor (diferencia documentada con el UML). |
| 3 | Usuario | Un `str` cualquiera podría guardarse como `password_hash` y terminar siendo una contraseña en texto plano. | El constructor solo acepta strings con formato de hash bcrypt; no existe accesor público al hash. |
| 4 | Usuario | `tienePermiso(modulo: Modulo)` usa el tipo `Modulo`, que no existe en el UML. | No se inventó la clase: queda como TODO para decidir con el equipo. |
| 5 | Departamento / Proyecto | Devolver la lista interna permitiría `depto.empleados.append(x)`, saltándose las reglas de asignación. | Los accesores devuelven una copia de la lista. |
| 6 | Departamento | Sin control, un mismo gerente podría quedar a cargo de dos departamentos (rompe la multiplicidad 0..1). | `cambiar_gerente()` lanza `OperacionNoPermitidaError` y libera al gerente anterior. |
| 7 | Validaciones | Repetir las mismas reglas (texto vacío, email, montos > 0) en cada clase duplicaría código. | Se centralizaron en `ecotech/modelos/_validaciones.py`. |
| 8 | Validaciones | `True` pasa como número en Python (`bool` es subclase de `int`), así que `salario=True` sería válido. | `validar_positivo` y `__validar_horas` rechazan `bool` explícitamente. |
| 9 | Prueba | Una etiqueta del script decía "Salario negativo" pero probaba con 0. | Se corrigió el texto. |

### Decisión

- [x] ADOPTAR (provisoria, decisión delegada en la IA; pendiente de revisión del equipo en el PR)
- [ ] MODIFICAR
- [ ] DESCARTAR

### Criterio (seguridad, eficiencia, coherencia con UML)

- **Seguridad:** atributos privados con `__`; sin setters para ID, hash ni registros de horas; el salario solo existe cifrado; el usuario solo guarda el hash bcrypt; las listas internas no se exponen.
- **Coherencia con UML:** se respetan las clases, atributos, herencias y multiplicidades del Anexo A. Las diferencias (parámetro `cifrado`, `crear_usuario()`, IDs provisorios, validación de asignación en RegistroTiempo) quedan documentadas en `docs/modelo-uml-vs-codigo.md`.
- **Eficiencia / reutilización:** validaciones escritas una sola vez; Gerente reutiliza todo Empleado con `super()`; `__str__` se define una vez en Persona y usa el `obtener_resumen()` de cada subclase.
- **Verificación:** `python -m tests.prueba_modelo` ejecuta 33 comprobaciones, todas OK.

### Código final o commit

```
(pendiente: commit lo realiza el equipo)
```
