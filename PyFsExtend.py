import pathlib as pl
from .PyFsBasic import *


def GoThroughDir(dirObj: Dir, FileHandler: function):
    def Dfs(parentRoot: pl.PurePath, subFiles: list[File]):
        for fileObj in subFiles:
            childPath = parentRoot.joinpath(fileObj.name)

            FileHandler(fileObj, childPath)

            if type(fileObj) == Dir:
                Dfs(childPath, fileObj.subFiles)

    relativeRootPath = pl.PurePath('/')
    FileHandler(dirObj, relativeRootPath)
    Dfs(relativeRootPath, dirObj.subFiles)