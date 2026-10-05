DROP TRIGGER IF EXISTS fn_historial_ticket_insert;
DELIMITER //
CREATE TRIGGER fn_historial_ticket_insert
AFTER INSERT ON fn_tickets
FOR EACH ROW
BEGIN
    INSERT INTO fn_historial_ticket (ticket_id, estado_anterior, estado_nuevo)
    VALUES (NEW.id, NULL, NEW.estado);
END//
DELIMITER ;

DROP TRIGGER IF EXISTS fn_actualizar_ticket;
DELIMITER //
CREATE TRIGGER fn_actualizar_ticket
BEFORE UPDATE ON fn_tickets
FOR EACH ROW
BEGIN
    SET NEW.actualizado_en = CURRENT_TIMESTAMP;
    IF NEW.estado = 'Cerrado' AND OLD.estado <> 'Cerrado' THEN
        SET NEW.cerrado_en = CURRENT_TIMESTAMP;
    ELSEIF NEW.estado <> 'Cerrado' THEN
        SET NEW.cerrado_en = NULL;
    END IF;
END//
DELIMITER ;

DROP TRIGGER IF EXISTS fn_historial_ticket_update;
DELIMITER //
CREATE TRIGGER fn_historial_ticket_update
AFTER UPDATE ON fn_tickets
FOR EACH ROW
BEGIN
    IF NOT (OLD.estado <=> NEW.estado) THEN
        INSERT INTO fn_historial_ticket (ticket_id, estado_anterior, estado_nuevo)
        VALUES (NEW.id, OLD.estado, NEW.estado);
    END IF;
END//
DELIMITER ;

INSERT INTO fn_historial_ticket (ticket_id, estado_anterior, estado_nuevo, cambiado_en)
SELECT t.id, NULL, t.estado, t.creado_en
FROM fn_tickets t
WHERE NOT EXISTS (
    SELECT 1 FROM fn_historial_ticket h WHERE h.ticket_id = t.id
);
