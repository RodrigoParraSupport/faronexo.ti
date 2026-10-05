INSERT IGNORE INTO fn_empleados (nombre, correo, rol) VALUES
    ('Camila Rojas', 'camila.rojas@faronexo.local', 'solicitante'),
    ('Mateo Fuentes', 'mateo.fuentes@faronexo.local', 'solicitante'),
    ('Isidora Leiva', 'isidora.leiva@faronexo.local', 'ambos'),
    ('Leonor Salgado', 'leonor.salgado@faronexo.local', 'tecnico'),
    ('Gaspar Mella', 'gaspar.mella@faronexo.local', 'tecnico');

INSERT IGNORE INTO fn_perfil_empleado (empleado_id, departamento, extension, sede)
SELECT id,
       CASE correo
           WHEN 'camila.rojas@faronexo.local' THEN 'Operaciones'
           WHEN 'mateo.fuentes@faronexo.local' THEN 'Personas'
           WHEN 'isidora.leiva@faronexo.local' THEN 'Finanzas'
           ELSE 'Tecnologia'
       END,
       CASE WHEN rol IN ('tecnico', 'ambos') THEN '410' ELSE '220' END,
       'Santiago'
FROM fn_empleados
WHERE correo LIKE '%@faronexo.local';

INSERT IGNORE INTO fn_especialidades (nombre, descripcion) VALUES
    ('Equipos y periféricos', 'Diagnóstico de estaciones, impresoras y accesorios'),
    ('Redes y conectividad', 'Acceso a red, VPN y conectividad corporativa'),
    ('Aplicaciones internas', 'Herramientas de trabajo y sistemas institucionales'),
    ('Cuentas y accesos', 'Identidades, permisos y autenticación');

INSERT IGNORE INTO fn_empleado_especialidad (empleado_id, especialidad_id, nivel)
SELECT e.id, s.id,
       CASE WHEN s.nombre = 'Redes y conectividad' THEN 'Avanzado' ELSE 'Intermedio' END
FROM fn_empleados e CROSS JOIN fn_especialidades s
WHERE e.correo = 'leonor.salgado@faronexo.local'
  AND s.nombre IN ('Redes y conectividad', 'Cuentas y accesos');

INSERT IGNORE INTO fn_empleado_especialidad (empleado_id, especialidad_id, nivel)
SELECT e.id, s.id,
       CASE WHEN s.nombre = 'Aplicaciones internas' THEN 'Avanzado' ELSE 'Intermedio' END
FROM fn_empleados e CROSS JOIN fn_especialidades s
WHERE e.correo = 'gaspar.mella@faronexo.local'
  AND s.nombre IN ('Aplicaciones internas', 'Equipos y periféricos');

INSERT INTO fn_tickets (asunto, descripcion, prioridad, solicitante_id, tecnico_id)
SELECT 'Acceso intermitente al portal',
       'El portal interno pierde la sesión varias veces durante la jornada.',
       'Alta', s.id, t.id
FROM fn_empleados s CROSS JOIN fn_empleados t
WHERE s.correo = 'camila.rojas@faronexo.local'
  AND t.correo = 'leonor.salgado@faronexo.local'
  AND NOT EXISTS (
      SELECT 1 FROM fn_tickets WHERE asunto = 'Acceso intermitente al portal'
  );

INSERT IGNORE INTO fn_ticket_especialidad (ticket_id, especialidad_id)
SELECT t.id, e.id FROM fn_tickets t CROSS JOIN fn_especialidades e
WHERE t.asunto = 'Acceso intermitente al portal'
  AND e.nombre = 'Redes y conectividad';
