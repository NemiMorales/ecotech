"""Punto de entrada del sistema EcoTech Solutions.

Ejecutar desde la raíz del repo:  python main.py
"""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from ecotech.datos.conexion import Conexion
from ecotech.excepciones import EcoTechError
from ecotech.interfaz.menu import Aplicacion
from ecotech.seguridad.cifrado import ServicioCifrado


# IA: adoptado
def configurar_log() -> None:
    """Los detalles técnicos de los errores van a un archivo, nunca a la pantalla."""
    carpeta = Path(__file__).parent / "logs"
    carpeta.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=carpeta / "ecotech.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )


def main() -> int:
    configurar_log()
    load_dotenv()  # lee el .env: credenciales y claves fuera del código
    try:
        cifrado = ServicioCifrado.desde_entorno()
        conexion = Conexion()
        conexion.probar()
        Aplicacion(conexion, cifrado).iniciar()
    except EcoTechError as error:
        print(f"✖ No se pudo iniciar: {error}")
        if "FERNET_KEY" in str(error):
            print('  Genere una con: python -c "from cryptography.fernet import Fernet; '
                  'print(Fernet.generate_key().decode())"')
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma finalizado.")
    except Exception:
        logging.exception("Error no controlado al iniciar")
        print("✖ Error inesperado. El detalle quedó registrado en logs/ecotech.log.")
        return 1
    print("Hasta pronto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
