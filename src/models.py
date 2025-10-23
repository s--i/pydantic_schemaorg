from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class PydanticBase(BaseModel):
    name: str
    description: str
    valid_name: Optional[str] = None

    model_config = ConfigDict()

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        name = self.name
        if not name:
            raise ValueError()
        if name in {
            "class",
            "def",
            "from",
            "import",
            "return",
            "yield",
            "True",
            "False",
        }:
            valid_name = f"{name}_"
        elif name[0].isdigit():
            valid_name = f"_{name}"
        else:
            valid_name = name
        object.__setattr__(self, "valid_name", valid_name)


class PydanticField(PydanticBase):
    type: str


class Import(BaseModel):
    type: str
    classPath: str
    classes_: set


class PydanticClass(PydanticBase):
    fields: List[PydanticField]
    parents: List['PydanticClass']
    depth: int = 1
    parent_imports: List[Import]
    field_imports: List[Import]
    pydantic_imports: List[Import] = []
    forward_refs: List[Import] = []
    filename: str = ""

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        if not self.valid_name:
            raise ValueError()
        filename = self.valid_name
        if filename in {
            "class",
            "def",
            "from",
            "import",
            "return",
            "yield",
        }:
            filename = f"{filename}_"
        object.__setattr__(self, "filename", filename)


PydanticClass.model_rebuild()
