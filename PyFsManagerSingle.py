from PyFsBasic import *


class FsManagerSingle(FsManager):
    def __init__(self, loadData:dict=None):
        if (loadData != None) and (loadData[PACK_TAG_fs_type] != PACK_TAG_FS_TYPE_single):
            raise FsError(ERROR_TYPE_ERROR, loadData[PACK_TAG_fs_type], (PACK_TAG_FS_TYPE_single,))
        else:
            super().__init__(loadData)


    def PackData(self):
        data = super().PackData()
        data[PACK_TAG_fs_type] = PACK_TAG_FS_TYPE_single


    def GetFileObj(self, path: PurePath):
        if IsRootPath(path):
            return self.rootDir

        splitPath = SplitPath(path)

        fileTree = self.rootDir.subFiles
        for i, name in enumerate(splitPath):
            isLast = (i == (len(splitPath)-1))
            found = False
            for file_ in fileTree:
                if file_.name == name:
                    # 已是最后一级
                    if isLast:
                        return file_

                    # 未到最后一级
                    else:
                        if type(file_) == Dir:
                            fileTree = file_.subFiles
                            found = True
                            break
                        else:
                            errorPath = PurePath(*splitPath[:i+1])
                            raise FsError(ERROR_IS_NOT_DIR, errorPath)

            if not found:
                if isLast:
                    raise FsError(ERROR_NOT_EXIST, PurePath(*splitPath))
                else:
                    errorPath = PurePath(*splitPath[:i+1])
                    raise FsError(ERROR_NOT_EXIST, errorPath)


    def CreateFile(self, path: PurePath, type_):
        if not issubclass(type_, File):
            raise FsError(ERROR_TYPE_ERROR, type_, (File, Dir))

        if IsRootPath(path):
            raise FsError(ERROR_IS_ROOT_PATH, path)

        parentDir = self.GetFileObj(path.parent)
        if type(parentDir) != Dir:
            raise FsError(ERROR_IS_NOT_DIR, path.parent)

        for file_ in parentDir.subFiles:
            if (file_.name == path.name):
                raise FsError(ERROR_ALREADY_EXIST, path)

        fileObj = type_(path.name)
        parentDir.subFiles.append(fileObj)

        return fileObj


    def DeleteFile(self, path: PurePath):
        if IsRootPath(path):
            raise FsError(ERROR_IS_ROOT_PATH, path)

        parentDir = self.GetFileObj(path.parent)
        if type(parentDir) != Dir:
            raise FsError(ERROR_IS_NOT_DIR, path.parent)

        for i, file_ in enumerate(parentDir.subFiles):
            if (file_.name == path.name):
                del parentDir.subFiles[i]
                return file_

        raise FsError(ERROR_NOT_EXIST, path)


    def MoveFile(self, sourcePath: PurePath, targetPath: PurePath):
        if IsRootPath(sourcePath):
            raise FsError(ERROR_IS_ROOT_PATH, sourcePath)
        if IsRootPath(targetPath):
            raise FsError(ERROR_IS_ROOT_PATH, targetPath)

        sourceParentDir = self.GetFileObj(sourcePath.parent)
        if type(sourceParentDir) != Dir:
            raise FsError(ERROR_IS_NOT_DIR, sourceParentDir.parent)

        for i, file_ in enumerate(sourceParentDir.subFiles):
            if (file_.name == sourcePath.name):
                sourceFile = file_
                del sourceParentDir.subFiles[i]

                try:
                    targetParentDir = self.GetFileObj(targetPath.parent)
                    if type(targetParentDir) != Dir:
                        raise FsError(ERROR_IS_NOT_DIR, targetPath.parent)

                    for file_ in targetParentDir.subFiles:
                        if (file_.name == targetPath.name):
                            raise FsError(ERROR_ALREADY_EXIST, targetPath)

                    sourceFile.Rename(targetPath.name)
                    targetParentDir.subFiles.append(sourceFile)

                except FsError as error:
                    sourceParentDir.subFiles.append(sourceFile)
                    errorInfo = error.args
                    if (errorInfo[0] == ERROR_NOT_EXIST) \
                      and (SplitPath(errorInfo[1]) == SplitPath(sourcePath)) \
                      and (type(sourceFile) == Dir):
                        raise FsError(ERROR_CANNOT_MOVE_INTO_ITSELF, sourcePath, targetPath)

                    else:
                        raise error

                return sourceFile

        raise FsError(ERROR_NOT_EXIST, sourcePath)


    def CopyFile(self, sourcePath: PurePath, targetPath: PurePath):
        if IsRootPath(targetPath):
            raise FsError(ERROR_IS_ROOT_PATH, targetPath)

        sourceFile = self.GetFileObj(sourcePath)

        targetParentDir = self.GetFileObj(targetPath.parent)
        if type(targetParentDir) != Dir:
            raise FsError(ERROR_IS_NOT_DIR, targetPath.parent)

        for file_ in targetParentDir.subFiles:
            if (file_.name == targetPath.name):
                raise FsError(ERROR_ALREADY_EXIST, targetPath)

        targetFile = deepcopy(sourceFile)
        targetFile.Rename(targetPath.name)
        targetParentDir.subFiles.append(targetFile)

        return targetFile