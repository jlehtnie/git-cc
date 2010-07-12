from common import *
from os.path import join, dirname, islink
from os import symlink, rmdir

class Status:
    def __init__(self, files):
        self.setFile(files[0])
    def setFile(self, file):
        self.file = file
    def cat(self):
        blob = git_exec(['cat-file', 'blob', getBlob(self.id, self.file)], decode=False)
	if islink(self.file):
	   # TODO: can symlink be mkelem'd or do we need to use cleartool ln -s ?
	   symlink(blob, join(CC_DIR, self.file))
	else:
            write(join(CC_DIR, self.file), blob)
    def stageDirs(self, t):
        dir = dirname(self.file)
        dirs = []
        while not exists(join(CC_DIR, dir)):
            dirs.append(dir)
            dir = dirname(dir)
        self.dirs = dirs
        t.stageDir(dir)
    def commitDirs(self, t):
        while len(self.dirs) > 0:
            dir = self.dirs.pop();
            if not exists(join(CC_DIR, dir)):
                cc_exec(['mkelem', '-nc', '-eltype', 'directory', dir])
                t.add(dir)

class Modify(Status):
    def stage(self, t):
        t.stage(self.file)
    def commit(self, t):
        self.cat()

class Add(Status):
    def stage(self, t):
        self.stageDirs(t)
    def commit(self, t):
        self.commitDirs(t)
        self.cat()
        cc_exec(['mkelem', '-nc', self.file])
        t.add(self.file)

class Delete(Status):
    def stage(self, t):
        t.stageDir(dirname(self.file))
    def commit(self, t):
        cc_exec(['rm', self.file])
	print "file: %s" % self.file
	print "dir: %s" % dirname(self.file)
	dir = dirname(self.file)
	try:
	    while dir:
	    	rmdir(join(CC_DIR, dir))
		# TODO: ct rm dir?
		# TODO: avoid checkin in removed dirs?
	    	dir = dirname(dir)
	except OSError:
	    print "dir is %s not empty" % dir

class Rename(Status):
    def __init__(self, files):
        self.old = files[0]
        self.new = files[1]
        self.setFile(self.new)
    def stage(self, t):
        t.stageDir(dirname(self.old))
        t.stage(self.old)
        self.stageDirs(t)
    def commit(self, t):
        self.commitDirs(t)
        cc_exec(['mv', '-nc', self.old, self.new])
        t.checkedout.remove(self.old)
        t.add(self.new)
        self.cat()
