"""
ROL 4 — HITL & Trust Flow
Simulación del voice bot de verificación de identidad.
"""


VOICE_BOT_SCRIPT = """
Hola, le contactamos de su banco.
Hemos detectado una transacción inusual en su cuenta.
Por favor, confirme si usted autorizó esta operación.
Presione 1 para CONFIRMAR o 2 para CANCELAR la transacción.
"""


def run_voice_bot():
    """
    Simula una llamada automatizada de verificación de identidad.
    En producción, aquí se integraría con Twilio, AWS Connect, etc.
    """
    # TODO: Integrar con proveedor de telefonía (Twilio, AWS Connect)
    print("[VoiceBot] Iniciando llamada automatizada...")
    print(VOICE_BOT_SCRIPT)
    print("[VoiceBot] Simulación completada.")
