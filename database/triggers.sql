-- Función para evitar sesiones en el pasado
CREATE OR REPLACE FUNCTION evitar_sesion_pasada()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.fecha_proyeccion < NOW() THEN
        RAISE EXCEPTION 'No se puede programar una sesión en el pasado';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger BEFORE INSERT
CREATE TRIGGER trg_evitar_sesion_pasada
BEFORE INSERT ON sesiones
FOR EACH ROW
EXECUTE FUNCTION evitar_sesion_pasada();

-- Función para registrar anfitrión como asistente
CREATE OR REPLACE FUNCTION registrar_anfitrion_como_asistente()
RETURNS TRIGGER AS $$ 
BEGIN
    INSERT INTO asistencias (id_sesion, id_miembro, confirmado)
    VALUES (NEW.id, NEW.anfitrion_id, TRUE);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger AFTER INSERT
CREATE TRIGGER trg_registrar_anfitrion
AFTER INSERT ON sesiones
FOR EACH ROW
EXECUTE FUNCTION registrar_anfitrion_como_asistente();
