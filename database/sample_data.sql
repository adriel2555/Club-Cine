-- Miembros
INSERT INTO miembros (nombre, email) VALUES
('Ana Pérez', 'ana@cineclub.com'),
('Luis Rojas', 'luis@cineclub.com'),
('Sofía Díaz', 'sofia@cineclub.com');

-- Películas
INSERT INTO peliculas (titulo, director, ano_lanzamiento, sinopsis, url_poster) VALUES
('La Llegada', 'Denis Villeneuve', 2016, 'Una lingüista trabaja con extraterrestres para salvar el mundo.', 'https://link-poster.com/llegada.jpg'),
('Parásitos', 'Bong Joon-ho', 2019, 'Una familia pobre se infiltra en una rica.', 'https://link-poster.com/parasitos.jpg'),
('Amélie', 'Jean-Pierre Jeunet', 2001, 'Una chica encuentra formas únicas de ayudar a los demás.', 'https://link-poster.com/amelie.jpg'),
('El Padrino', 'Francis Ford Coppola', 1972, 'La historia de una familia mafiosa.', 'https://link-poster.com/padrino.jpg'),
('Interstellar', 'Christopher Nolan', 2014, 'Viajes espaciales y relatividad.', 'https://link-poster.com/interstellar.jpg');

-- Sesión de prueba
SELECT programar_nueva_sesion('La Llegada', 'Denis Villeneuve', NOW() + INTERVAL '2 days', 'Auditorio Principal', 1);
