import pathlib
import PyFsBasic as pfb
import json
import os




#a.CreateFile(pathlib.PurePath('/a'), pfb.File)
#a.CreateFile(pathlib.PurePath('/b'), pfb.Dir)
#a.CreateFile(pathlib.PurePath('/a'), pfb.Dir)
#a.MoveFile(pathlib.PurePath('/a'), pathlib.PurePath('/a/1'), pfb.File)
#exit()
hashList = set()
def BuildFileTree(FsHandler: pfb.FsManager, path):
    fh = FsHandler

    for file_ in path.iterdir():
        fp = pathlib.PurePath(*pfb.SplitPath(file_)[len(srp):])
        if file_.is_dir():
            fo = fh.CreateFile(fp, pfb.Dir)
            BuildFileTree(fh, file_)
        elif file_.is_file():
            fo = fh.CreateFile(fp, pfb.File)
            fileHash = GetFileHash(file_)
            hashList.add(fileHash)
            fo.info = (os.path.getsize(file_), fileHash)


a = pfb.FsManager()



root = pathlib.Path('G:\\MC')
srp = pfb.SplitPath(root)

print('building start!')
BuildFileTree(a, root)
hashList = list(hashList)
rootObj = a.GetFileObj(pathlib.Path('/'), pfb.Dir)
rootObj.info = hashList
print('building finished!')
data = a.PackData()
filename='G:\\FileTree.json'
with open(filename, 'w') as file_obj:
    json.dump(data, file_obj)