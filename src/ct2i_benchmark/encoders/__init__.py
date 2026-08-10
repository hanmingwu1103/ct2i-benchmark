"""Encoder registry. Thin per-concept modules keep architecture separation."""
from .base import Encoder, MinMaxScaler01
from .unsupervised import LabelEncoder, OneHotEncoder01, CountEncoder
from .supervised import TargetEncoder, WoEEncoder, OrderedCatBoostEncoder
from .hashing_enc import ColumnAwareHashEncoder, SharedValueHashEncoder
from .homals import HomalsEncoder

REGISTRY = {
    "label": LabelEncoder,
    "onehot": OneHotEncoder01,
    "count": CountEncoder,
    "target": TargetEncoder,
    "woe": WoEEncoder,
    "ordered_catboost": OrderedCatBoostEncoder,
    "hash_column": ColumnAwareHashEncoder,
    "hash_shared": SharedValueHashEncoder,
    "homals": HomalsEncoder,
}

SUPERVISED = {"target", "woe", "ordered_catboost"}

__all__ = ["Encoder", "MinMaxScaler01", "REGISTRY", "SUPERVISED",
           "LabelEncoder", "OneHotEncoder01", "CountEncoder", "TargetEncoder",
           "WoEEncoder", "OrderedCatBoostEncoder", "ColumnAwareHashEncoder",
           "SharedValueHashEncoder", "HomalsEncoder"]
