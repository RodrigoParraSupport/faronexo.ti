DROP PROCEDURE IF EXISTS fn_cerrar_ticket;
DELIMITER //
CREATE PROCEDURE fn_cerrar_ticket(IN p_ticket_id BIGINT, IN p_resolucion TEXT)
BEGIN
    DECLARE v_estado VARCHAR(20) DEFAULT NULL;

    IF p_resolucion IS NULL OR CHAR_LENGTH(TRIM(p_resolucion)) < 10 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'La resolución debe tener al menos 10 caracteres.';
    END IF;

    SELECT estado INTO v_estado
      FROM fn_tickets
     WHERE id = p_ticket_id
     FOR UPDATE;

    IF v_estado IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No existe el ticket indicado.';
    END IF;
    IF v_estado = 'Cerrado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El ticket ya está cerrado.';
    END IF;

    UPDATE fn_tickets
       SET estado = 'Cerrado', resolucion = TRIM(p_resolucion)
     WHERE id = p_ticket_id;
END//
DELIMITER ;
