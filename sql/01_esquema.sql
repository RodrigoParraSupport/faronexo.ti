CREATE TABLE IF NOT EXISTS fn_empleados (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    correo VARCHAR(180) NOT NULL UNIQUE,
    rol VARCHAR(16) NOT NULL CHECK (rol IN ('solicitante', 'tecnico', 'ambos')),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS fn_perfil_empleado (
    empleado_id BIGINT NOT NULL PRIMARY KEY,
    departamento VARCHAR(100) NOT NULL,
    extension VARCHAR(12),
    sede VARCHAR(100) NOT NULL DEFAULT 'Casa matriz',
    CONSTRAINT fk_perfil_empleado FOREIGN KEY (empleado_id)
        REFERENCES fn_empleados(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS fn_especialidades (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    descripcion VARCHAR(240)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS fn_empleado_especialidad (
    empleado_id BIGINT NOT NULL,
    especialidad_id BIGINT NOT NULL,
    nivel VARCHAR(20) NOT NULL DEFAULT 'Intermedio'
        CHECK (nivel IN ('Inicial', 'Intermedio', 'Avanzado')),
    PRIMARY KEY (empleado_id, especialidad_id),
    CONSTRAINT fk_ee_empleado FOREIGN KEY (empleado_id)
        REFERENCES fn_empleados(id) ON DELETE CASCADE,
    CONSTRAINT fk_ee_especialidad FOREIGN KEY (especialidad_id)
        REFERENCES fn_especialidades(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS fn_tickets (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    asunto VARCHAR(140) NOT NULL,
    descripcion TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Abierto'
        CHECK (estado IN ('Abierto', 'En progreso', 'En espera', 'Cerrado')),
    prioridad VARCHAR(12) NOT NULL DEFAULT 'Media'
        CHECK (prioridad IN ('Baja', 'Media', 'Alta', 'Urgente')),
    solicitante_id BIGINT NOT NULL,
    tecnico_id BIGINT,
    resolucion TEXT,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cerrado_en TIMESTAMP NULL,
    CONSTRAINT chk_ticket_asunto CHECK (CHAR_LENGTH(TRIM(asunto)) >= 5),
    CONSTRAINT chk_ticket_descripcion CHECK (CHAR_LENGTH(TRIM(descripcion)) >= 10),
    CONSTRAINT chk_ticket_cierre CHECK (
        estado <> 'Cerrado' OR (resolucion IS NOT NULL AND CHAR_LENGTH(TRIM(resolucion)) >= 10)
    ),
    CONSTRAINT fk_ticket_solicitante FOREIGN KEY (solicitante_id)
        REFERENCES fn_empleados(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ticket_tecnico FOREIGN KEY (tecnico_id)
        REFERENCES fn_empleados(id) ON DELETE SET NULL,
    INDEX ix_tickets_estado_prioridad (estado, prioridad),
    INDEX ix_tickets_solicitante (solicitante_id),
    INDEX ix_tickets_tecnico (tecnico_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS fn_ticket_especialidad (
    ticket_id BIGINT NOT NULL,
    especialidad_id BIGINT NOT NULL,
    PRIMARY KEY (ticket_id, especialidad_id),
    CONSTRAINT fk_te_ticket FOREIGN KEY (ticket_id)
        REFERENCES fn_tickets(id) ON DELETE CASCADE,
    CONSTRAINT fk_te_especialidad FOREIGN KEY (especialidad_id)
        REFERENCES fn_especialidades(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS fn_historial_ticket (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    estado_anterior VARCHAR(20),
    estado_nuevo VARCHAR(20) NOT NULL,
    cambiado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historial_ticket FOREIGN KEY (ticket_id)
        REFERENCES fn_tickets(id) ON DELETE CASCADE,
    INDEX ix_historial_ticket_fecha (ticket_id, cambiado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
