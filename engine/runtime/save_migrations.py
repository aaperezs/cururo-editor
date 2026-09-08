from engine.entities.save_manager import SAVE_VERSION

# Registro de migraciones: version -> función de migración
# Cada función recibe el dict del save y lo modifica in-place.
MIGRATIONS = {
    # Ejemplo futuro:
    # 1: lambda data: _migrate_v1_to_v2(data),
}


def migrar(save_payload: dict):
    """Aplica migraciones en cadena desde la version del save hasta SAVE_VERSION."""
    current_version = save_payload.get("version", 1)
    while current_version < SAVE_VERSION:
        migration_fn = MIGRATIONS.get(current_version)
        if migration_fn is None:
            break
        migration_fn(save_payload)
        current_version += 1
        save_payload["version"] = current_version
