-- ================================
-- A. DISEÑO DE LA BASE DE DATOS
-- ================================

-- Tabla: miembros
CREATE TABLE miembros (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    fecha_union DATE DEFAULT CURRENT_DATE
);

-- Tabla: peliculas
CREATE TABLE peliculas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    director VARCHAR(100),
    ano_lanzamiento INTEGER,
    sinopsis TEXT,
    url_poster VARCHAR(255)
);

-- Tabla: sesiones
CREATE TABLE sesiones (
    id SERIAL PRIMARY KEY,
    id_pelicula INTEGER REFERENCES peliculas(id),
    fecha_proyeccion TIMESTAMP NOT NULL,
    lugar VARCHAR(255),
    anfitrion_id INTEGER REFERENCES miembros(id)
);

-- Tabla: asistencias
CREATE TABLE asistencias (
    id SERIAL PRIMARY KEY,
    id_sesion INTEGER REFERENCES sesiones(id),
    id_miembro INTEGER REFERENCES miembros(id),
    confirmado BOOLEAN DEFAULT FALSE,
    UNIQUE(id_sesion, id_miembro)
);
