import os

for folder in os.walk("ka-lite"):
    for name in folder[2]:
        if len(name) > 50:
            base, ext = os.path.splitext(name)
            if ext == ".py":
                base = base[0:50-len(ext)]
                print "Shortening '%s' to '%s'." % (name, base + ext)
                os.rename(os.path.join(folder[0], name), os.path.join(folder[0], base + ext))
