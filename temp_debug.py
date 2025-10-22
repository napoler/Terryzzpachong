import libtorrent as lt

s = lt.session()
settings = s.get_settings()
for k, v in settings.items():
    print(k)
