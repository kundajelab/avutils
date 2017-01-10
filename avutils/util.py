import sys, os
import os.path
from collections import OrderedDict
import numpy as np
import random
import json
import re


class GetBest(object):
    def __init__(self):
        self.best_object = None
        self.best_val = None

    def process(self, the_object, val):
        replace = self.best_object==None or self.is_better(val)
        if (replace):
            self.best_object = the_object
            self.best_val = val 
        return replace

    def is_better(self, val):
        raise NotImplementedError()

    def get_best(self):
        return self.best_object, self.best_val

    def get_best_val(self):
        return self.best_val

    def get_best_obj(self):
        return self.best_object


class GetBestMax(GetBest):
    def is_better(self, val):
        return val > self.best_val


class GetBestMin(GetBest):
    def is_better(self, val):
        return val < self.best_val


def init_get_best(larger_is_better):
    if (larger_is_better):
        return GetBestMax()
    else:
        return GetBestMin()


class VariableWrapper():
    """ For when I want reference-type access to an immutable"""
    def __init__(self, var):
        self.var = var   


class DefaultOrderedDictWrapper(object):
    def __init__(self, factory):
        self.ordered_dict = OrderedDict()
        assert hasattr(factory, '__call__')
        self.factory = factory

    def __getitem__(self, key):
        if key not in self.ordered_dict:
            self.ordered_dict[key] = self.factory() 
        return self.ordered_dict[key]


def one_hot_encode_sequences(sequences):
    return np.array([seq_to_2d_image(seq) for seq in sequences])


def theano_seq_to_2d_image(sequence):
    #theano dim ordering, uses row axis for one-hot
    to_return = np.zeros((1,4,len(sequence)), dtype=np.int8)
    seq_to_one_hot_fill_in_array(zeros_array=to_return[0],
                                 sequence=sequence, one_hot_axis=0)
    return to_return


def seq_to_2d_image(sequence, dim_ordering='th'):
    assert dim_ordering=='th', "tensorflow ordering not implemented yet"
    return theano_seq_to_2d_image(sequence)


def seq_to_one_hot(sequence): 
    #assumes 1d and tensorflow dim ordering
    to_return = np.zeros((len(sequence),4), dtype=np.int8)
    seq_to_one_hot_fill_in_array(to_return, sequence, one_hot_axis=1)
    return to_return


# Letter as 1, other letters as 0
def seq_to_one_hot_fill_in_array(zeros_array, sequence, one_hot_axis):
    assert one_hot_axis==0 or one_hot_axis==1
    if (one_hot_axis==0):
        assert zeros_array.shape[1] == len(sequence)
    elif (one_hot_axis==1): 
        assert zeros_array.shape[0] == len(sequence)
    #zeros_array should be an array of dim 4xlen(sequence), filled with zeros.
    #will mutate zeros_array
    for (i,char) in enumerate(sequence):
        if (char=="A" or char=="a"):
            char_idx = 0
        elif (char=="C" or char=="c"):
            char_idx = 1
        elif (char=="G" or char=="g"):
            char_idx = 2
        elif (char=="T" or char=="t"):
            char_idx = 3
        elif (char=="N" or char=="n"):
            continue #leave that pos as all 0's
        else:
            raise RuntimeError("Unsupported character: "+str(char))
        if (one_hot_axis==0):
            zeros_array[char_idx,i] = 1
        elif (one_hot_axis==1):
            zeros_array[i,char_idx] = 1


def enum(**enums):
    class Enum(object):
        pass
    to_return = Enum
    for key,val in enums.items():
        if hasattr(val, '__call__'): 
            setattr(to_return, key, staticmethod(val))
        else:
            setattr(to_return, key, val)
    to_return.vals = [x for x in enums.values()]
    to_return.the_dict = enums
    return to_return


def combine_enums(*enums):
    new_enum_dict = OrderedDict()
    for an_enum in enums:
        new_enum_dict.update(an_enum.the_dict)
    return enum(**new_enum_dict)


def get_random_string(size):
    import string
    return ''.join(random.choice(
                   string.ascii_letters+string.digits) for _ in range(size))


def format_as_json(jsonable_data):
    return json.dumps(jsonable_data, indent=4, separators=(',', ': '))


def get_core_file_name(file_name):
    return get_file_name_parts(file_name).core_file_name


def get_file_name_parts(file_name):
    p = re.compile(r"^(.*/)?([^\./]+)(\.[^/]*)?$")
    m = p.search(file_name)
    return FileNameParts(m.group(1), m.group(2), m.group(3))


def file_exists(file_path):
    return os.path.isfile(file_path)


def dir_exists(dir_path):
    return os.path.isdir(dir_path)


def create_dir_if_not_exists(dir_path):
    if (dir_exists(dir_path)==False):
        os.makedirs(dir_path) 


class FileNameParts(object):

    def __init__(self, directory, core_file_name, extension):
        self.directory = directory if (directory is not None) else os.getcwd()
        self.core_file_name = core_file_name
        self.extension = extension

    def get_full_path(self):
        return self.directory+"/"+self.file_name

    def get_core_file_name_and_extension(self):
        return self.core_file_name+self.extension

    def get_transformed_core_file_name(self, transformation, extension=None):
        to_return = transformation(self.core_file_name)
        if (extension is not None):
            to_return = to_return + extension
        else:
            if (self.extension is not None):
                to_return = to_return + self.extension
        return to_return

    def get_transformed_file_path(self, transformation, extension=None):
        return (self.directory+"/"+
                self.get_transformed_core_file_name(transformation,
                                                    extension=extension))


#randomly shuffles the input arrays (correspondingly)
#mutates arrs!
def shuffle_arrays(arrs, copy_on_shuffle):
    if len(arrs) == 0:
        raise ValueError("should supply at least one input array")
    len_of_arrs = len(arrs[0])
    #sanity check that all lengths are equal
    for arr in arrs:
        if (len(arr) != len_of_arrs):
            raise ValueError("First supplied array had length "
                             +str(len_of_arrs)
                             +" but a subsequent array had length "
                             +str(len(arr)))
    for i in xrange(0,len_of_arrs):
        #randomly select index:
        chosen_index = random.randint(i,len_of_arrs-1)
        for arr in arrs:
            #swap
            if (copy_on_shuffle):
                val_at_index = np.copy(arr[chosen_index])
                arr[chosen_index] = np.copy(arr[i])
                arr[i] = val_at_index
            else:
                val_at_index = arr[chosen_index]
                arr[chosen_index] = arr[i]
                arr[i] = val_at_index
    return arrs


def send_email(subject, to_addresses,
               sender, #eg: "avutils-mail-sender@stanford.edu",
               smtp_server, #eg: "smtp.stanford.edu",
               contents=""):
    from email.mime.text import MIMEText
    import smtplib
    msg = MIMEText(contents)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ",".join(to_addresses)

    s = smtplib.SMTP(smtp_server)
    s.starttls();
    s.sendmail(sender, to_addresses, msg.as_string())
    s.quit()


def chain_functions(*functions):
    if (len(functions) < 2):
        raise ValueError("input to chain_functions should "
                          "have at least two arguments")
    def chained_functions(x):
        x = functions[0](x)
        for function in functions[1:]:
            x = function(x)
        return x;
    return chainedFunctions
