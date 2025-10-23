from datetime import time, datetime, date
from decimal import Decimal
from typing import Any, Optional, ForwardRef, List, Union, Set
from typing import get_args, get_origin

from pydantic import BaseModel, Field, StrictBool, AnyUrl, StrictInt, StrictFloat, ConfigDict

from pydantic_schemaorg.ISO8601.ISO8601Date import ISO8601Date
from pydantic_schemaorg.__types__ import types

updated_models: Set[type] = set()

class SchemaOrgBase(BaseModel):
    #JSON-LD fields
    reverse_ : Optional[Any] = Field(default=None,alias='@reverse')
    id_ : Optional[Any] = Field(default=None,alias='@id')
    context_ : Optional[Any] = Field(default=None,alias='@context')
    graph_ : Optional[Any] = Field(default=None,alias='@graph')

    model_config = ConfigDict(populate_by_name=True)

    def model_dump(self, *args, **kwargs):
        defaults = {
            "exclude_none": True,
            "by_alias": True
        }
        return super().model_dump(*args, **dict(defaults, **kwargs))

    def model_dump_json(self, *args, **kwargs):
        defaults = {
            "exclude_none": True,
            "by_alias": True
        }
        return super().model_dump_json(*args, **dict(defaults, **kwargs))

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)

    def json(self, *args, **kwargs):
        return self.model_dump_json(*args, **kwargs)

    @classmethod
    def get_classes_for_forward_ref(cls, field: Any) -> List[tuple]:
        classes = []
        annotation = getattr(field, 'annotation', None)
        if annotation is None:
            return classes

        refs: Set[str] = set()

        def collect_forward_refs(annotation_value: Any) -> None:
            if isinstance(annotation_value, ForwardRef):
                refs.add(annotation_value.__forward_arg__)
                return
            forward_arg = getattr(annotation_value, '__forward_arg__', None)
            if forward_arg:
                refs.add(forward_arg)
                return
            origin = get_origin(annotation_value)
            if origin is None:
                return
            for arg in get_args(annotation_value):
                collect_forward_refs(arg)

        collect_forward_refs(annotation)

        for ref in refs:
            if ref in types:
                pydanticschema_org_type = types[ref]
                mod = __import__(pydanticschema_org_type[1], fromlist=[pydanticschema_org_type[0]])
                class_ = getattr(mod, pydanticschema_org_type[0])
                classes.append((ref, class_))
        return classes

    @classmethod
    def get_local_ns(cls):
        localns = {}
        fields = getattr(cls, 'model_fields', {})
        for k, v in fields.items():
            classes = cls.get_classes_for_forward_ref(v)
            for class_name, class_ in classes:
                localns.update({class_name: class_})
        return localns

    @classmethod
    def update_forward_refs(cls, **localns: Any) -> None:
        """
        Try to update ForwardRefs on fields based on this Model, globalns and localns.
        """
        if cls in updated_models:
            return
        namespace = {'Optional': Optional, 'List': List, 'Union': Union, 'StrictBool': StrictBool, 'AnyUrl': AnyUrl,
                     'Decimal': Decimal, 'time': time, 'datetime': datetime, 'date': date, 'ISO8601Date': ISO8601Date,
                     'StrictInt': StrictInt, 'StrictFloat': StrictFloat}
        namespace.update(localns)
        for cls_ in cls.mro():
            if hasattr(cls_, 'get_local_ns'):
                namespace.update(cls_.get_local_ns())
        cls.model_rebuild(_types_namespace=namespace, _parent_namespace_depth=2)
        updated_models.add(cls)

    def __init__(__pydantic_self__, **data: Any) -> None:
        __pydantic_self__.update_forward_refs()
        fields = getattr(type(__pydantic_self__), 'model_fields', {})
        for k in data.keys():
            if k in fields:
                field = fields[k]
                classes = __pydantic_self__.get_classes_for_forward_ref(field)
                for _, class_ in classes:
                    class_.update_forward_refs()
        super().__init__(**data)
