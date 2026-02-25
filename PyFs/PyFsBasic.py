from pathlib import PurePath, Path
from copy import deepcopy


PACK_TAG_INFO = 'info'
PACK_TAG_TYPE = 'type'
PACK_TAG_NAME = 'name'
PACK_TAG_SUBFILES = 'subFiles'
PACK_TAG_TYPE_FILE = 'File'
PACK_TAG_TYPE_DIR = 'Dir'
PACK_TAG_FS_TYPE = 'FsType'
PACK_TAG_FILE_TREE = 'FileTree'
# PACK_TAG_FS_TYPE_NORMAL = 'normal'
# PACK_TAG_FS_TYPE_SINGLE = 'single'

NAME_ROOT_DIR = '/'

class FsError(Exception): pass

ERROR_NOT_EXIST = 'ERROR_not_exist'
ERROR_ALREADY_EXIST = 'ERROR_already_exist'
ERROR_IS_ROOT_PATH = 'ERROR_is_root_path'
ERROR_TYPE_ERROR = 'ERROR_type_error'
ERROR_ILLEGAL_FILE_NAME = 'ERROR_illegal_fileName'
ERROR_CANNOT_MOVE_INTO_ITSELF = 'ERROR_cannot_move_into_itself'
# ERROR_IS_NOT_DIR = 'ERROR_is_not_dir' # 仅在Single中使用


# 会忽略“/”，“./”，Windows驱动器号等，不会忽略“..”
def SplitPath(path: Path):
    splitPath = []
    for i in path.parents:
        if i.name != '':
            splitPath.insert(0, i.name)
    if path.name != '':
        splitPath.append(path.name)
    return splitPath


def IsRootPath(path: Path):
    for parent in path.parents:
        if parent.name != '':
            return False
    if path.name != '':
        return False
    return True


def CheckFileName(fileName: str):
    FILE_NAME_blackChars = ('/', '\\', ':', '*', '?', '"', '<', '>', '|')

    if (fileName[-1] == ' ') or (fileName.strip(' ') == ''):
        return False

    for i in FILE_NAME_blackChars:
        if i in fileName:
            return False

    return True



class File:
    def __init__(self, name: str=None, loadData:dict=None):
        if loadData != None:
            self.__Load(loadData)
        else:
            self.name = None
            self.info = None

        if name != None:
            self.Rename(name)


    def Rename(self, newName: str):
        if self.name == NAME_ROOT_DIR:
            raise FsError(ERROR_IS_ROOT_PATH, PurePath('/'))

        if type(newName) != str:
            raise FsError(ERROR_TYPE_ERROR, newName, (str,))

        #''' 应让用户选择 是否检查合法性 以及 检查的标准
        if CheckFileName(newName) == False:
            raise FsError(ERROR_ILLEGAL_FILE_NAME, newName)
        #'''

        self.name = newName


    def Pack(self):
        data = {
            PACK_TAG_TYPE: CLASS_TAG[type(self)],
            PACK_TAG_NAME: self.name,
            PACK_TAG_INFO: self.info,
        }

        return data


    def __Load(self, data):
        if TAG_CLASS[data[PACK_TAG_TYPE]] != type(self):
            pass
            # raise FsError(ERROR_TYPE_ERROR, data[PACK_TAG_TYPE], (CLASS_TAG[type(self)],))
        self.name = data[PACK_TAG_NAME]
        self.info = data[PACK_TAG_INFO]



class Dir(File):
    def __init__(self, name: str=None, loadData:dict=None):
        super().__init__(name, loadData)
        self.subFiles = []
        if loadData != None:
            self.__Load(loadData)


    def Pack(self):
        data = super().Pack()

        subFilesData = []
        for sFile in self.subFiles:
            subFilesData.append(sFile.Pack())
        data[PACK_TAG_SUBFILES] = subFilesData

        return data


    def __Load(self, data):
        subFilesData = data[PACK_TAG_SUBFILES]
        for fileData in subFilesData:
            type_ = TAG_CLASS[fileData[PACK_TAG_TYPE]]
            obj = type_(loadData=fileData)
            self.subFiles.append(obj)



TAG_CLASS = {
    PACK_TAG_TYPE_DIR: Dir,
    PACK_TAG_TYPE_FILE: File
}

CLASS_TAG = {v:k for k,v in TAG_CLASS.items()}



class FsManagerBasic:
    def __init__(self, loadData: dict=None):
        if loadData is not None:
            fileTree = loadData[PACK_TAG_FILE_TREE]
            self.rootDir = Dir(loadData=fileTree)

        else:
            # 创建根目录
            rootDir = Dir()
            rootDir.name = NAME_ROOT_DIR
            self.rootDir = rootDir


    def PackData(self):
        data = {
            PACK_TAG_FS_TYPE: None, # 保留字段
            PACK_TAG_FILE_TREE: self.rootDir.Pack()
        }

        return data


    def GetFileObj(self, path: PurePath, type_):
        if not issubclass(type_, File):
            raise FsError(ERROR_TYPE_ERROR, type_, (File, Dir))

        if IsRootPath(path):
            if type_ != Dir:
                # 要获取 根目录 必须用 Dir
                raise FsError(ERROR_NOT_EXIST, path, type_)
            else:
                return self.rootDir

        splitPath = SplitPath(path)

        fileTree = self.rootDir.subFiles
        for i, name in enumerate(splitPath):
            isLast = (i == (len(splitPath)-1))
            found = False
            for file_ in fileTree:
                if file_.name == name:
                    fileType = type(file_)

                    # 已是最后一级
                    if isLast:
                        if fileType == type_:
                            return file_

                    # 未到最后一级
                    else:
                        if fileType == Dir:
                            fileTree = file_.subFiles
                            found = True
                            break

            if not found:
                if isLast:
                    raise FsError(ERROR_NOT_EXIST, PurePath(*splitPath), type_)
                else:
                    errorPath = PurePath(*splitPath[:i+1])
                    raise FsError(ERROR_NOT_EXIST, errorPath, Dir)


    def CreateFile(self, path: PurePath, type_):
        if not issubclass(type_, File):
            raise FsError(ERROR_TYPE_ERROR, type_, (File, Dir))

        if IsRootPath(path):
            raise FsError(ERROR_IS_ROOT_PATH, path)

        parentDir = self.GetFileObj(path.parent, Dir)

        for file_ in parentDir.subFiles:
            if (file_.name == path.name) and (type(file_) == type_):
                raise FsError(ERROR_ALREADY_EXIST, path, type(file_)) # 返回已存在的那个文件的类型

        fileObj = type_(path.name)
        parentDir.subFiles.append(fileObj)

        return fileObj


    def DeleteFile(self, path: PurePath, type_):
        if not issubclass(type_, File):
            raise FsError(ERROR_TYPE_ERROR, type_, (File, Dir))

        if IsRootPath(path):
            raise FsError(ERROR_IS_ROOT_PATH, path)

        parentDir = self.GetFileObj(path.parent, Dir)

        for i, file_ in enumerate(parentDir.subFiles):
            if (file_.name == path.name) and (type(file_) == type_):
                del parentDir.subFiles[i]
                return file_

        raise FsError(ERROR_NOT_EXIST, path, type_)


    def MoveFile(self, sourcePath: PurePath, targetPath: PurePath, type_):
        if not issubclass(type_, File):
            raise FsError(ERROR_TYPE_ERROR, type_, (File, Dir))

        if IsRootPath(sourcePath):
            raise FsError(ERROR_IS_ROOT_PATH, sourcePath)
        if IsRootPath(targetPath):
            raise FsError(ERROR_IS_ROOT_PATH, targetPath)

        sourceParentDir = self.GetFileObj(sourcePath.parent, Dir)

        for i, file_ in enumerate(sourceParentDir.subFiles):
            if (file_.name == sourcePath.name) and (type(file_) == type_):
                sourceFile = file_
                del sourceParentDir.subFiles[i]

                try:
                    targetParentDir = self.GetFileObj(targetPath.parent, Dir)

                    for file_ in targetParentDir.subFiles:
                        if (file_.name == targetPath.name) and (type(file_) == type_):
                            raise FsError(ERROR_ALREADY_EXIST, targetPath, type(file_)) # 返回已存在的那个文件的类型

                    sourceFile.Rename(targetPath.name)
                    targetParentDir.subFiles.append(sourceFile)

                except FsError as error:
                    sourceParentDir.subFiles.append(sourceFile)
                    errorInfo = error.args
                    if (errorInfo[0] == ERROR_NOT_EXIST) \
                      and (SplitPath(errorInfo[1]) == SplitPath(sourcePath)) \
                      and (type(sourceFile) == Dir):
                        raise FsError(ERROR_CANNOT_MOVE_INTO_ITSELF, sourcePath, targetPath ,type(sourceFile))

                    else:
                        raise error

                return sourceFile

        raise FsError(ERROR_NOT_EXIST, sourcePath, type_)


    def CopyFile(self, sourcePath: PurePath, targetPath: PurePath, type_):
        if not issubclass(type_, File):
            raise FsError(ERROR_TYPE_ERROR, type_, (File, Dir))

        if IsRootPath(targetPath):
            raise FsError(ERROR_IS_ROOT_PATH, targetPath)

        sourceFile = self.GetFileObj(sourcePath, type_)

        targetParentDir = self.GetFileObj(targetPath.parent, Dir)

        for file_ in targetParentDir.subFiles:
            if (file_.name == targetPath.name) and (type(file_) == type_):
                raise FsError(ERROR_ALREADY_EXIST, targetPath, type(file_)) # 返回已存在的那个文件的类型

        targetFile = deepcopy(sourceFile)
        targetFile.Rename(targetPath.name)
        targetParentDir.subFiles.append(targetFile)

        return targetFile


import json.decoder

__all__ = ['SplitPath',
           'IsRootPath',
           'CheckFileName',
           'File',
           'Dir',
           'FsManagerBasic',
           'FsError'
           ]