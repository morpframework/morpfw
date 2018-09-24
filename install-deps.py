import os

TARBALLS = {
    'elasticsearch':
    ('https://artifacts.elastic.co/downloads/elasticsearch/'
     'elasticsearch-5.6.2.tar.gz')
}

os.chdir(os.path.abspath(os.path.dirname(__file__)))
if not os.path.exists('downloads/'):
    os.mkdir('downloads')
if not os.path.exists('opt/'):
    os.mkdir('opt')
for d, u in TARBALLS.items():
    print("Installing %s" % d)
    basename = os.path.basename(u)
    if not os.path.exists('downloads/%s' % basename):
        os.system('wget %s -O downloads/%s' % (u, basename))
    if not os.path.exists('opt/%s' % d):
        os.mkdir('opt/%s' % d)
        os.system('tar xvf downloads/%s -C opt/%s' % (basename, d))

print("Install Completed")
