from collections import OrderedDict

class DynamicEnum(object):
    """
        just a wrapper around a dictionary, so that the keys are
        accessible using the object attribute syntax rather
        than the dictionary syntax.
    """
    def __init__(self):
        self._vals_dict = OrderedDict()

    def add_key(self, key_name, val):
        setattr(self, key_name, val)
        self._vals_dict[key_name] = val

    def get_key(self, key_name):
        return self._vals_dict[key_name]

    def has_key(self, key_name):
        if key_name not in self._vals_dict:
            return False;
        return True;

    def get_keys(self):
        return self._vals_dict.keys()


class UNDEF(object):
    pass


class Key(object):
    def __init__(self, key_name_internal,
                       key_name_external=None, default=UNDEF):
        self.key_name_internal = key_name_internal
        if (key_name_external is None):
            key_name_external = key_name_internal
        self.key_name_external = key_name_external
        self.default = default


#I am keeping a different external and internal name
#for the flexibility of changing the external name in the future.
#the advantage of having a class like this rather than just
#using enums is being able to support methods like "fill_in_defaults_for_keys".
#I need the DynamicEnum class so that I can use the Keys class for
#different types of Keys; i.e. I don't
#know what the keys are going to be beforehand and I don't know
#how else to create an enum dynamically.
class Keys(object): 
    def __init__(self, *keys):
        #just a wrapper around a dictionary, for the
        #purpose of accessing the keys using the object
        #attribute syntax rather than the dictionary syntax.
        self.keys = DynamicEnum() 
        self.k = self.keys
        self.keys_defaults = DynamicEnum()
        for key in keys:
            self.add_key(key.key_name_internal, key.key_name_external,
                         key.default)

    def add_key(self, key_name_internal,
                      key_name_external, default_value=UNDEF):
        self.keys.add_key(key_name_internal, key_name_external)
        if (default_value != UNDEF):
            self.keys_defaults.add_key(key_name_internal, default_value)

    def get_keys(self):
        return self.k.get_keys()

    def check_for_unsupported_keys(self, a_dict):
        for a_key in a_dict:
            if self.keys.has_key(a_key)==False:
                raise RuntimeError("Unsupported key "+str(a_key)
                                   +"; supported keys are: "
                                   +str(self.keys.get_keys()))

    def fill_in_defaults_for_keys(self,
        a_dict, internal_names_of_keys_to_fill_defaults_for=None):
        if internal_names_of_keys_to_fill_defaults_for is None:
            internal_names_of_keys_to_fill_defaults_for = self.keys.get_keys()
        for a_key in internal_names_of_keys_to_fill_defaults_for:
            if a_key not in a_dict:
                if (self.keys_defaults.has_key(a_key)==False):
                    raise RuntimeError("Default for "+str(a_key)
                                       +" not present, and a value "
                                       +"was not provided")
                a_dict[a_key] = self.keys_defaults.get_key(a_key);
        return a_dict;

    def check_for_unsupported_keys_and_fill_in_defaults(self, a_dict):
        self.check_for_unsupported_keys(a_dict)
        self.fill_in_defaults_for_keys(a_dict);
