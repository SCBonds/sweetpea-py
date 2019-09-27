from typing import Any, Type, List, Tuple, Union, cast
from itertools import product, chain, repeat
import random


"""
Helper function which grabs names from derived levels;
    if the level is non-derived the level *is* the name
"""
def get_internal_level_name(level: Any) -> Any:
    return level.internal_name

def get_external_level_name(level: Any) -> Any:
    return level.external_name

class __Primitive:
    def require_type(self, label: str, type: Type, value: Any):
        if not isinstance(value, type):
            raise ValueError(label + ' must be a ' + str(type) + '.')


    def require_non_empty_list(self, label: str, value: Any):
        self.require_type(label, List, value)
        if len(value) == 0:
            raise ValueError(label + ' must not be empty.')

    def __str__(self):
        raise Exception("Attempted implicit string cast of primitive")

class SimpleLevel(__Primitive):
    def __init__(self, name):
        self.external_name = str(name)
        self.internal_name = str(name) + "{:05d}".format(random.randint(0, 99999))
        self.__validate()

    def __validate(self):
        if not (hasattr(self.external_name, "__eq__")):
            raise ValueError("Level names must be comparable, but received "
                             + str(self.external_name))

    def __str__(self):
        raise Exception("Attempted implicit string cast of simple level")

    def __eq__(self, other):
        if (type(other) != SimpleLevel):
            print("Attempted to compare a simple level to another type, " + str(type(other)))
        return other.internal_name == self.internal_name


class DerivedLevel(__Primitive):
    def __init__(self, name, window):
        self.external_name = str(name)
        self.internal_name = str(name) + "{:05d}".format(random.randint(0, 99999))
        self.window = window
        self.__validate()
        self.__expand_window_arguments()

    def __validate(self):
        self.require_type('DerivedLevel.external_name', str, self.external_name)
        window_type = type(self.window)
        allowed_window_types = [WithinTrial, Transition, Window]
        if window_type not in allowed_window_types:
            raise ValueError('DerivedLevel.window must be one of ' +
                str(allowed_window_types) + ', but was ' + str(window_type) + '.')

        #if len(set(map(lambda f: f.factor_name, self.window.args))) != len(self.window.args):
            #raise ValueError('Factors should not be repeated in the argument list to a derivation function.')

        for f in filter(lambda f: f.is_derived(), self.window.args):
            w = f.levels[0].window
            if not (w.width == 1 and w.stride == 1):
                raise ValueError("Derived levels may only be derived from factors that apply to each trial. '" +
                    self.external_name + "' cannot derive from '" + f.factor_name + "'")

        # TODO: Windows should be uniform.

    def __expand_window_arguments(self) -> None:
        self.window.args = list(chain(*[list(repeat(arg, self.window.width)) for arg in self.window.args]))

    def get_dependent_cross_product(self) -> List[Tuple[Any, ...]]:
        return list(product(*[[(dependent_factor, x) for x in dependent_factor.levels] for dependent_factor in self.window.args]))

    def __eq__(self, other):
        if (type(other) != DerivedLevel):
            print("Attempted to compare a derived level to another type, " + str(type(other)))
        return self.internal_name == other.internal_name

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


class Factor(__Primitive):
    def __init__(self, name: str, levels) -> None:
        self.factor_name = name
        self.levels = self.__make_levels(levels)
        self.__validate()

    def __make_levels(self, levels):
        out_levels = []
        self.require_non_empty_list('Factor.levels', levels)
        for level in levels:
            if isinstance(level, DerivedLevel):
                out_levels.append(level)
            else:
                out_levels.append(SimpleLevel(level))
        return out_levels

    def __validate(self):
        self.require_type('Factor.factor_name', str, self.factor_name)
        level_type = type(self.levels[0])
        if level_type not in [SimpleLevel, DerivedLevel]:
            raise ValueError('Factor.levels must be either SimpleLevel or DerivedLevel')

        for l in self.levels:
            if type(l) != level_type:
                raise ValueError('Expected all levels to be ' + str(level_type) +
                    ', but found ' + str(type(l)) + '.')

        if level_type == DerivedLevel:
            window_type = type(self.levels[0].window)
            for dl in self.levels:
                if type(dl.window) != window_type:
                    raise ValueError('Expected all DerivedLevel.window types to be ' +
                        str(window_type) + ', but found ' + str(type(dl)) + '.')

    def is_derived(self) -> bool:
        return isinstance(self.levels[0], DerivedLevel)

    def has_complex_window(self) -> bool:
        if not self.is_derived():
            return False

        window = self.levels[0].window
        return window.width > 1 or window.stride > 1

    def get_level(self, level_name: str) -> Union[SimpleLevel, DerivedLevel]:
        for l in self.levels:
            if l.internal_name == level_name:
                return l
        return cast(SimpleLevel, None)

    def has_level(self, level: Any) -> bool:
        return (level in self.levels)

    def __hash__(self):
        return(hash(self.factor_name))

    """
    Returns true if this factor applies to the given trial number. (1-based)
    For example, Factors with Transition windows in the derived level don't apply
    to Trial 1, but do apply to all subsequent trials.
    """
    def applies_to_trial(self, trial_number: int) -> bool:
        if trial_number <= 0:
            raise ValueError('Trial numbers may not be less than 1')

        if not self.is_derived():
            return True

        window = self.levels[0].window
        return trial_number >= window.width and (trial_number - window.width) % window.stride == 0

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


class __BaseWindow():
    def __init__(self, fn, args, width: int, stride: int) -> None:
        self.fn = fn
        self.args = args
        self.argc = len(args)
        self.width = width
        self.stride = stride
        # TODO: validation
        # TODO: args should all be factors


"""
TODO: Docs
"""
class WithinTrial(__Primitive, __BaseWindow):
    def __init__(self, fn, args):
        super().__init__(fn, args, 1, 1)
        # TODO: validation

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


"""
TODO: Docs
"""
class Transition(__Primitive, __BaseWindow):
    def __init__(self, fn, args):
        super().__init__(fn, args, 2, 1)
        # TODO: validation

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


class Window(__Primitive, __BaseWindow):
    def __init__(self, fn, args, width, stride):
        super().__init__(fn, args, width, stride)
        # TODO: validation

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
