import sqlite3
c = sqlite3.connect('corazon_melodico.db')
c.execute("DROP TABLE IF EXISTS requests_saas")
c.execute("DROP TABLE IF EXISTS songs_saas")
c.execute("DROP TABLE IF EXISTS bars")
c.commit()

from db import init_db
init_db()

c.execute("INSERT INTO songs_saas (bar_id, title, artist, album, genre, lyrics) SELECT 'bar_1', title, artist, album, genre, lyrics FROM songs")
c.commit()
