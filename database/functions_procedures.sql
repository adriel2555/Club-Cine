-- Procedimiento: programar_nueva_sesion
CREATE OR REPLACE FUNCTION programar_nueva_sesion(
    titulo_pelicula VARCHAR,
    director_pelicula VARCHAR,
    fecha_p TIMESTAMP,
    lugar_p VARCHAR,
    id_anfitrion INT
) RETURNS INTEGER AS $$
DECLARE
    id_pelicula INT;
    id_sesion INT;
BEGIN
    SELECT id INTO id_pelicula FROM peliculas
    WHERE titulo = titulo_pelicula AND director = director_pelicula;

    IF id_pelicula IS NULL THEN
        INSERT INTO peliculas (titulo, director)
        VALUES (titulo_pelicula, director_pelicula)
        RETURNING id INTO id_pelicula;
    END IF;

    INSERT INTO sesiones (id_pelicula, fecha_proyeccion, lugar, anfitrion_id)
    VALUES (id_pelicula, fecha_p, lugar_p, id_anfitrion)
    RETURNING id INTO id_sesion;

    RETURN id_sesion;
END;
$$ LANGUAGE plpgsql;

-- Procedimiento: confirmar_asistencia
CREATE OR REPLACE PROCEDURE confirmar_asistencia(
    id_sesion_p INT,
    id_miembro_p INT
)
LANGUAGE plpgsql AS $$
BEGIN
    IF (SELECT fecha_proyeccion FROM sesiones WHERE id = id_sesion_p) < NOW() THEN
        RAISE EXCEPTION 'No se puede confirmar asistencia a una sesión pasada';
    END IF;

    INSERT INTO asistencias (id_sesion, id_miembro, confirmado)
    VALUES (id_sesion_p, id_miembro_p, TRUE);
END;
$$;

-- Función: obtener historial de películas vistas
CREATE OR REPLACE FUNCTION obtener_historial_peliculas_vistas_por_miembro(
    id_miembro_p INT
)
RETURNS TABLE(titulo VARCHAR, fecha_proyeccion DATE) AS $$
BEGIN
    RETURN QUERY
    SELECT p.titulo, s.fecha_proyeccion::DATE
    FROM asistencias a
    JOIN sesiones s ON a.id_sesion = s.id
    JOIN peliculas p ON s.id_pelicula = p.id
    WHERE a.id_miembro = id_miembro_p AND a.confirmado = TRUE;
END;
$$ LANGUAGE plpgsql;
